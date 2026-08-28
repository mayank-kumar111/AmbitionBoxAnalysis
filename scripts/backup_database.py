"""Create and restore portable backups of the SQLite history database."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def backup_database(database: Path, destination: Path) -> Path:
    if not database.exists():
        raise FileNotFoundError(f"Database not found: {database}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(database, destination)
    return destination


def restore_database(backup: Path, database: Path) -> Path:
    if not backup.exists():
        raise FileNotFoundError(f"Backup not found: {backup}")
    database.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(backup, database)
    return database


def main() -> int:
    parser = argparse.ArgumentParser(description="Backup or restore the AmbitionBox SQLite history database.")
    parser.add_argument("--database", type=Path, default=Path("data/ambitionbox.db"))
    parser.add_argument("--backup", type=Path, required=True)
    parser.add_argument("--restore", action="store_true", help="Restore the database from --backup")
    args = parser.parse_args()

    if args.restore:
        restore_database(args.backup, args.database)
        print(f"Restored database: {args.database}")
    else:
        backup_database(args.database, args.backup)
        print(f"Created database backup: {args.backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
