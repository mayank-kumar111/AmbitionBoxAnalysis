from pathlib import Path

import pandas as pd

from scripts.refresh_history import main as refresh_main


def test_refresh_history_seeds_and_imports(tmp_path, monkeypatch):
    master = tmp_path / "master.csv"
    incoming_dir = tmp_path / "incoming"
    incoming_dir.mkdir()
    database = tmp_path / "history.db"
    report = tmp_path / "report.json"

    frame = pd.DataFrame([
        {
            "company_name": "Example Corp",
            "company_rating": 4.0,
            "industry": "IT",
            "size": "1k-5k Employees",
            "type": "Private",
            "years_old": 10,
            "location": "Jaipur",
        }
    ])
    master.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(master, index=False)
    frame.to_csv(incoming_dir / "snapshot.csv", index=False)

    monkeypatch.setattr(
        "sys.argv",
        [
            "refresh_history.py",
            "--master", str(master),
            "--incoming", str(incoming_dir),
            "--database", str(database),
            "--snapshot-at", "2026-08-27T19:00:00+00:00",
            "--report", str(report),
        ],
    )

    refresh_main()

    assert database.exists()
    assert report.exists()

    from src.database.sqlite_store import SQLiteStore

    store = SQLiteStore(database)
    assert store.company_count() == 1
    assert store.snapshot_count() == 2
    assert store.refresh_run_count() == 1

    dashboard_history = Path("ambitionbox_app/static/refresh_history.json")
    assert dashboard_history.exists()
