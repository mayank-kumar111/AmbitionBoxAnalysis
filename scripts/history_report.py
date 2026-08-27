"""Generate a human-readable report from the SQLite history database."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow ``python scripts/history_report.py ...`` to work from the repository root.
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.analytics.history import HistoricalAnalytics


def main() -> None:
    parser = argparse.ArgumentParser(description="Report historical AmbitionBox changes.")
    parser.add_argument("database", type=Path, help="SQLite database path")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    analytics = HistoricalAnalytics(args.database)

    print("\n=== SNAPSHOT SUMMARY ===")
    print(analytics.snapshot_summary().to_string(index=False))

    print("\n=== MOST IMPROVED COMPANIES ===")
    improved = analytics.most_improved_companies(limit=args.limit)
    print(improved.to_string(index=False) if not improved.empty else "No rating improvements recorded.")

    print("\n=== NEW COMPANIES ===")
    new = analytics.new_companies(limit=args.limit)
    print(new.to_string(index=False) if not new.empty else "No new companies recorded.")

    print("\n=== LATEST CHANGES ===")
    changes = analytics.latest_changes(limit=args.limit)
    print(changes.to_string(index=False) if not changes.empty else "No changes recorded.")


if __name__ == "__main__":
    main()
