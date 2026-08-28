"""Validate a SQLite history database and restore a last-known-good backup."""

from __future__ import annotations

import argparse
import shutil
import sqlite3
from pathlib import Path


def check_integrity(database: Path) -> tuple[bool, str]:
    if not database.exists():
        return False, "database file does not exist"
    try:
        with sqlite3.connect(database) as connection:
            result = connection.execute("PRAGMA integrity_check").fetchone()
    except sqlite3.Error as exc:
        return False, f"sqlite error: {exc}"
    message = str(result[0]) if result else "unknown integrity result"
    return message.lower() == "ok", message


def restore_if_needed(database: Path, backup: Path, *, force: bool = False) -> bool:
    healthy, reason = check_integrity(database)
    if healthy and not force:
        print(f"Database healthy: {database}")
        return False
    if not backup.exists():
        raise FileNotFoundError(f"Backup not found: {backup}")

    database.parent.mkdir(parents=True, exist_ok=True)
    if database.exists():
        corrupt_copy = database.with_suffix(database.suffix + ".corrupt")
        shutil.copy2(database, corrupt_copy)
        print(f"Saved unhealthy database as: {corrupt_copy}")

    shutil.copy2(backup, database)
    restored_ok, restored_reason = check_integrity(database)
    if not restored_ok:
        raise RuntimeError(f"Restored backup is also invalid: {restored_reason}")

    print(f"Restored last-known-good database: {database} ({reason})")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate SQLite history DB and optionally restore a backup.")
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--backup", type=Path, required=True)
    parser.add_argument("--force", action="store_true", help="Restore even when the database is healthy")
    args = parser.parse_args()

    try:
        restore_if_needed(args.database, args.backup, force=args.force)
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"ERROR: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
