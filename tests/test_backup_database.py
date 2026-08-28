from pathlib import Path

from scripts.backup_database import backup_database, restore_database


def test_backup_and_restore_round_trip(tmp_path):
    database = tmp_path / "data" / "ambitionbox.db"
    backup = tmp_path / "backup" / "ambitionbox.db.bak"
    database.parent.mkdir(parents=True)
    database.write_bytes(b"original-db")

    created = backup_database(database, backup)
    assert created == backup
    assert backup.read_bytes() == b"original-db"

    database.write_bytes(b"corrupted-db")
    restored = restore_database(backup, database)
    assert restored == database
    assert database.read_bytes() == b"original-db"


def test_backup_requires_existing_database(tmp_path):
    database = tmp_path / "missing.db"
    backup = tmp_path / "backup.db"

    try:
        backup_database(database, backup)
    except FileNotFoundError as exc:
        assert "Database not found" in str(exc)
    else:
        raise AssertionError("Expected FileNotFoundError")


def test_restore_requires_existing_backup(tmp_path):
    database = tmp_path / "database.db"
    backup = tmp_path / "missing.bak"

    try:
        restore_database(backup, database)
    except FileNotFoundError as exc:
        assert "Backup not found" in str(exc)
    else:
        raise AssertionError("Expected FileNotFoundError")
