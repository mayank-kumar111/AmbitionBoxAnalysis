"""CLI for historical company analytics."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.analytics.history import HistoricalAnalytics


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze AmbitionBox history.")
    parser.add_argument("--db", type=Path, default=Path("data/ambitionbox.db"))
    parser.add_argument("--company", help="Show history for one company")
    parser.add_argument("--location", help="Optional company location")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    analytics = HistoricalAnalytics(args.db)

    if args.company:
        history = analytics.company_history(args.company, args.location)
        print(history.to_string(index=False))
        return

    print("\n=== Snapshot Summary ===")
    print(analytics.snapshot_summary().to_string(index=False))
    print("\n=== Latest Changes ===")
    print(analytics.latest_changes(args.limit).to_string(index=False))
    print("\n=== Most Improved Companies ===")
    print(analytics.most_improved_companies(args.limit).to_string(index=False))
    print("\n=== New Companies ===")
    print(analytics.new_companies(args.limit).to_string(index=False))


if __name__ == "__main__":
    main()
