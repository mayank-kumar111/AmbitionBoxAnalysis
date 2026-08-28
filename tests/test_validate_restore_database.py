from pathlib import Path

from scripts.validate_and_restore_database import check_integrity, restore_if_needed


def _make_db(path: Path, value: str = "good") -> None:
    import sqlite3

    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE sample (value TEXT)")
        conn.execute("INSERT INTO sample(value) VALUES (?)", (value,))
        conn.commit()


def test_healthy_database_is_left_untouched(tmp_path):
    db = tmp_path / "history.db"
    backup = tmp_path / "backup.db"
    _make_db(db, "current")
    _make_db(backup, "backup")

    assert check_integrity(db)[0] is True
    assert restore_if_needed(db, backup) is False
    assert not (tmp_path / "history.db.corrupt").exists()


def test_corrupt_database_is_restored(tmp_path):
    db = tmp_path / "history.db"
    backup = tmp_path / "backup.db"
    _make_db(backup, "last-good")
    db.write_bytes(b"not a sqlite database")

    assert restore_if_needed(db, backup) is True
    assert check_integrity(db)[0] is True
    assert (tmp_path / "history.db.corrupt").exists()


def test_invalid_backup_fails(tmp_path):
    db = tmp_path / "history.db"
    backup = tmp_path / "backup.db"
    db.write_bytes(b"bad db")
    backup.write_bytes(b"also bad")

    try:
        restore_if_needed(db, backup)
    except RuntimeError as exc:
        assert "also invalid" in str(exc)
    else:
        raise AssertionError("Expected invalid backup to fail")
