"""Versioned backup and restore helper for the master companies CSV."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from datetime import datetime, timezone


def backup_master(master: str | Path, backup_dir: str | Path) -> Path:
    source = Path(master)
    if not source.exists():
        raise FileNotFoundError(f"Master dataset not found: {source}")
    destination_dir = Path(backup_dir)
    destination_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destination = destination_dir / f"companies-{stamp}.csv"
    shutil.copy2(source, destination)
    return destination


def restore_master(master: str | Path, backup: str | Path) -> None:
    source = Path(backup)
    if not source.exists():
        raise FileNotFoundError(f"Backup not found: {source}")
    destination = Path(master)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def main() -> int:
    parser = argparse.ArgumentParser(description="Backup or restore the master AmbitionBox CSV.")
    parser.add_argument("--master", default="ambitionbox_app/data/companies.csv")
    parser.add_argument("--backup-dir", default="data/backups/master")
    parser.add_argument("--restore", help="Restore from this backup CSV")
    args = parser.parse_args()

    if args.restore:
        restore_master(args.master, args.restore)
        print(f"Restored master dataset from: {args.restore}")
    else:
        path = backup_master(args.master, args.backup_dir)
        print(f"Created master dataset backup: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
