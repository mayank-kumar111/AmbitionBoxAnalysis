"""Build/update the local SQLite company database from a cleaned CSV."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow ``python scripts/build_database.py ...`` to work from the repository root.
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd

from src.database.sqlite_store import SQLiteStore
from src.preprocessing.validator import validate_or_raise


def main() -> None:
    parser = argparse.ArgumentParser(description="Load company data into SQLite.")
    parser.add_argument("input", type=Path, help="Cleaned company CSV")
    parser.add_argument("--database", type=Path, default=Path("data/ambitionbox.db"))
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    validate_or_raise(df)

    snapshot_at = datetime.now(timezone.utc).isoformat()
    store = SQLiteStore(args.database)
    store.initialize()
    count = store.import_dataframe(df, snapshot_at)

    print(f"Processed: {count:,} records")
    print(f"Companies in database: {store.company_count():,}")
    print(f"Snapshot records: {store.snapshot_count():,}")
    print(f"Database: {args.database}")


if __name__ == "__main__":
    main()
