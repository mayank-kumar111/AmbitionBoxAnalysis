"""Refresh the persistent SQLite history database from a newly collected snapshot.

The script is designed for both local use and GitHub Actions. On the first run it
seeds the database from the current master CSV; subsequent runs only import the
newly collected snapshot so historical state can accumulate across runs.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd

from scripts.update_dataset import load_snapshot_files
from src.database.sqlite_store import SQLiteStore
from src.preprocessing.validator import validate_or_raise


def _snapshot_exists(store: SQLiteStore, snapshot_at: str) -> bool:
    with store.connect() as connection:
        row = connection.execute(
            "SELECT 1 FROM company_snapshots WHERE snapshot_at = ? LIMIT 1",
            (snapshot_at,),
        ).fetchone()
    return row is not None


def _latest_snapshot(store: SQLiteStore) -> str | None:
    with store.connect() as connection:
        row = connection.execute("SELECT MAX(snapshot_at) FROM company_snapshots").fetchone()
    return row[0] if row and row[0] else None


def _seed_timestamp(snapshot_at: str) -> str:
    """Place a first-run baseline immediately before the incoming snapshot."""
    try:
        parsed = datetime.fromisoformat(snapshot_at.replace("Z", "+00:00"))
    except ValueError:
        parsed = datetime.now(timezone.utc)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return (parsed - timedelta(seconds=1)).isoformat()


def main() -> None:
    parser = argparse.ArgumentParser(description="Persist a collected snapshot in SQLite history.")
    parser.add_argument("--master", type=Path, required=True)
    parser.add_argument("--incoming", type=Path, required=True)
    parser.add_argument("--database", type=Path, default=Path("data/ambitionbox.db"))
    parser.add_argument("--snapshot-at", default=None, help="UTC timestamp for this snapshot")
    parser.add_argument("--report", type=Path, default=Path("reports/history_refresh.json"))
    args = parser.parse_args()

    store = SQLiteStore(args.database)
    store.initialize()

    snapshot_at = args.snapshot_at or datetime.now(timezone.utc).isoformat()
    seeded = False
    seed_records = 0

    if store.company_count() == 0:
        master = pd.read_csv(args.master)
        validate_or_raise(master)
        seed_time = _seed_timestamp(snapshot_at)
        if not _snapshot_exists(store, seed_time):
            seed_records = store.import_dataframe(master, seed_time)
            seeded = True

    incoming = load_snapshot_files(args.incoming)
    validate_or_raise(incoming, check_duplicates=False)

    imported = 0
    if not _snapshot_exists(store, snapshot_at):
        imported = store.import_dataframe(incoming, snapshot_at)

    report = {
        "database": str(args.database),
        "seeded_master": seeded,
        "seed_records": int(seed_records),
        "incoming_records": int(len(incoming)),
        "imported_snapshot_records": int(imported),
        "companies_in_database": store.company_count(),
        "snapshot_records_in_database": store.snapshot_count(),
        "latest_snapshot": _latest_snapshot(store),
        "incoming_directory": str(args.incoming),
    }

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
