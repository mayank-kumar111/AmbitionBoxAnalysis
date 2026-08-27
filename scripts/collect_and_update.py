"""Collect a fresh snapshot and prepare an incremental dataset update.

The command is dry-run by default. Scraped files are stored separately from
the application dataset, and the master dataset is only written with --apply.
"""

from __future__ import annotations

import argparse
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
    args = parser.parse_args()

    locations = EXTENDED_LOCATIONS if args.extended else CORE_LOCATIONS
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    incoming_dir = ROOT_DIR / "data" / "incoming" / timestamp

    config = ScraperConfig(pages=args.pages)
    scraper = AmbitionBoxScraper(config)
    scraper.scrape_locations(locations, incoming_dir)

    incoming = load_snapshot_files(incoming_dir)
    merged, result = IncrementalIngestor(args.master).merge(
        incoming,
        output_path=args.output if args.apply else None,
    )

    report = {
        "snapshot": timestamp,
        "locations": locations,
        "pages_per_location": args.pages,
        "previous_records": result.previous_records,
        "incoming_records": result.incoming_records,
        "final_records": result.final_records,
        "new_records": result.new_records,
        "updated_records": result.updated_records,
        "unchanged_records": result.unchanged_records,
        "invalid_records": result.invalid_records,
        "applied": args.apply,
        "incoming_directory": str(incoming_dir.relative_to(ROOT_DIR)),
    }

    args.report.parent.mkdir(parents=True, exist_ok=True)
    import json
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(report, indent=2))
    if not args.apply:
        print("DRY RUN: the master dataset was not changed. Use --apply to write the merged output.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    main()
