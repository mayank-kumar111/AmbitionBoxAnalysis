from pathlib import Path

from scripts.master_backup import backup_master, restore_master


def test_backup_and_restore_master(tmp_path):
    master = tmp_path / "companies.csv"
    backup_dir = tmp_path / "backups"
    master.write_text("company_name,company_rating\nA,4.1\n", encoding="utf-8")

    backup = backup_master(master, backup_dir)
    assert backup.exists()
    assert backup.read_text(encoding="utf-8") == master.read_text(encoding="utf-8")

    master.write_text("company_name,company_rating\nA,1.0\n", encoding="utf-8")
    restore_master(master, backup)
    assert "4.1" in master.read_text(encoding="utf-8")


def test_missing_master_fails(tmp_path):
    missing = tmp_path / "missing.csv"
    try:
        backup_master(missing, tmp_path / "backups")
    except FileNotFoundError as exc:
        assert "Master dataset not found" in str(exc)
    else:
        raise AssertionError("Expected FileNotFoundError")
