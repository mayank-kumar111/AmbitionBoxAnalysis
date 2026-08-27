"""Collect a fresh snapshot and prepare an incremental dataset update.

The command is dry-run by default. Scraped files are stored separately from
the application dataset, and the master dataset is only written with --apply.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.ingestion.incremental import IncrementalIngestor
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
    parser.add_argument("--apply", action="store_true", help="Write the merged dataset")
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
        output_path=args.output if args.apply else None,
        full_snapshot=args.full_snapshot,
    )

    report = result.to_dict()
    report["snapshot"] = timestamp
    report["locations"] = locations
    report["pages_per_location"] = args.pages
    report["new_companies"] = list(result.new_companies)
    report["updated_companies"] = list(result.updated_companies)
    report["applied"] = args.apply
    report["full_snapshot"] = args.full_snapshot
    report["incoming_directory"] = str(incoming_dir.relative_to(ROOT_DIR))

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    print(json.dumps(report, indent=2, default=str))
    if not args.apply:
        print("DRY RUN: the master dataset was not changed. Use --apply to write the merged output.")
    else:
        print(f"Merged dataset written to: {args.output}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    main()
