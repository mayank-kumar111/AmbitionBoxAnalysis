"""Collect a fresh snapshot and prepare an incremental dataset update."""

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
from src.quality.health import summarize_health
from src.scraper.ambitionbox_scraper import AmbitionBoxScraper
from src.scraper.config import ScraperConfig
from src.scraper.locations import CORE_LOCATIONS, EXTENDED_LOCATIONS
from scripts.update_dataset import load_snapshot_files

LOGGER = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect and incrementally update AmbitionBox data.")
    parser.add_argument("--master", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, default=Path("reports/update_report.json"))
    parser.add_argument("--pages", type=int, default=10)
    parser.add_argument("--extended", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--full-snapshot", action="store_true")
    args = parser.parse_args()

    if args.pages < 1:
        parser.error("--pages must be at least 1")

    locations = EXTENDED_LOCATIONS if args.extended else CORE_LOCATIONS
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    incoming_dir = ROOT_DIR / "data" / "incoming" / timestamp

    scraper = AmbitionBoxScraper(ScraperConfig(pages=args.pages))
    scraper.scrape_locations(locations, incoming_dir)

    incoming = load_snapshot_files(incoming_dir)
    ingestor = IncrementalIngestor(args.master)
    merged, result = ingestor.merge(incoming, output_path=None, full_snapshot=args.full_snapshot)

    rating_changes = sum(
        1 for company in result.updated_companies
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
    report.update({
        "snapshot": timestamp,
        "locations": locations,
        "pages_per_location": args.pages,
        "new_companies": list(result.new_companies),
        "updated_companies": list(result.updated_companies),
        "duplicate_records": duplicate_records,
        "rating_changes": rating_changes,
        "anomalies": [item.to_dict() for item in anomalies],
        "anomalies_found": bool(anomalies),
        "critical_anomalies": [item.to_dict() for item in critical_anomalies],
        "applied": applied,
        "full_snapshot": args.full_snapshot,
        "incoming_directory": str(incoming_dir.relative_to(ROOT_DIR)),
    })
    report["health"] = summarize_health(report)

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    dashboard_report = ROOT_DIR / "ambitionbox_app" / "static" / "last_update_report.json"
    dashboard_report.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(args.report, dashboard_report)

    print(json.dumps(report, indent=2, default=str))
    if critical_anomalies:
        print("ANOMALY BLOCK: critical anomalies were found; the master dataset was NOT changed.")
        if args.apply:
            raise SystemExit(2)
    elif not applied:
        print("DRY RUN: the master dataset was not changed. Use --apply to write the merged output.")
    else:
        print(f"Merged dataset written to: {args.output}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    main()
