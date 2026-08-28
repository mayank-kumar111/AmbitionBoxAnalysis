"""Collect a fresh snapshot and prepare an incremental dataset update.

The command is dry-run by default. Scraped files are stored separately from
the application dataset, and the master dataset is only written with --apply.
Critical anomalies block an --apply run until the input is reviewed.
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.ingestion.incremental import IncrementalIngestor
from src.quality.anomaly_detector import detect_anomalies
from src.scraper.ambitionbox_scraper import AmbitionBoxScraper
from src.scraper.config import ScraperConfig
from src.scraper.locations import CORE_LOCATIONS, EXTENDED_LOCATIONS
from scripts.update_dataset import load_snapshot_files

LOGGER = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect and incrementally update AmbitionBox data.")
    parser.add_argument("--master", type=Path, required=True, help="Current master CSV")
    parser.add_argument("--output", type=Path, required=True, help="Merged output CSV")
    parser.add_argument("--report", type=Path, default=Path("reports/update_report.json"))
    parser.add_argument("--pages", type=int, default=10, help="Maximum pages per location for this run")
    parser.add_argument("--extended", action="store_true", help="Include the extended location preset")
    parser.add_argument("--apply", action="store_true", help="Write the merged dataset when no critical anomaly is found")
    parser.add_argument("--full-snapshot", action="store_true", help="Report removals only when the collection covers the complete source")
    args = parser.parse_args()

    if args.pages < 1:
        parser.error("--pages must be at least 1")

    locations = EXTENDED_LOCATIONS if args.extended else CORE_LOCATIONS
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    incoming_dir = ROOT_DIR / "data" / "incoming" / timestamp

    config = ScraperConfig(pages=args.pages)
    scraper = AmbitionBoxScraper(config)
    scraper.scrape_locations(locations, incoming_dir)

    incoming = load_snapshot_files(incoming_dir)
    ingestor = IncrementalIngestor(args.master)
    merged, result = ingestor.merge(
        incoming,
        output_path=None,
        full_snapshot=args.full_snapshot,
    )

    rating_changes = sum(
        1
        for company in result.updated_companies
        if "company_rating" in company.get("changes", {})
    )
    duplicate_records = result.incoming_duplicate_rows + result.master_duplicate_keys

    anomalies = detect_anomalies(
        previous_records=result.previous_records,
        incoming_records=result.incoming_records,
        final_records=result.final_records,
        new_records=result.new_records,
        updated_records=result.updated_records,
        duplicate_records=duplicate_records,
        invalid_records=result.invalid_records,
        rating_changes=rating_changes,
        removed_records=result.removed_records if args.full_snapshot else None,
    )

    critical_anomalies = [item for item in anomalies if item.severity == "critical"]
    applied = False
    if args.apply and not critical_anomalies:
        destination = Path(args.output)
        destination.parent.mkdir(parents=True, exist_ok=True)
        merged.to_csv(destination, index=False)
        applied = True

    report = result.to_dict()
    report["snapshot"] = timestamp
    report["locations"] = locations
    report["pages_per_location"] = args.pages
    report["new_companies"] = list(result.new_companies)
    report["updated_companies"] = list(result.updated_companies)
    report["duplicate_records"] = duplicate_records
    report["rating_changes"] = rating_changes
    report["anomalies"] = [item.to_dict() for item in anomalies]
    report["anomalies_found"] = bool(anomalies)
    report["critical_anomalies"] = [item.to_dict() for item in critical_anomalies]
    report["applied"] = applied
    report["full_snapshot"] = args.full_snapshot
    report["incoming_directory"] = str(incoming_dir.relative_to(ROOT_DIR))

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    dashboard_report = ROOT_DIR / "ambitionbox_app" / "static" / "last_update_report.json"
    dashboard_report.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(args.report, dashboard_report)

    print(json.dumps(report, indent=2, default=str))
    if critical_anomalies:
        print("ANOMALY BLOCK: critical anomalies were found; the master dataset was NOT changed.")
    elif not applied:
        print("DRY RUN: the master dataset was not changed. Use --apply to write the merged output.")
    else:
        print(f"Merged dataset written to: {args.output}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    main()
