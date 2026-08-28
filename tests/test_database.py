import pandas as pd

from src.database.sqlite_store import SQLiteStore


def sample_dataframe() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "company_name": "Example Corp",
            "company_rating": 4.2,
            "industry": "IT Services",
            "size": "1k-5k Employees",
            "type": "Public",
            "years_old": 20,
            "location": "Jaipur",
        }
    ])


def test_sqlite_store_inserts_and_updates(tmp_path):
    store = SQLiteStore(tmp_path / "ambitionbox.db")
    store.initialize()

    assert store.import_dataframe(sample_dataframe(), "2026-08-27T10:00:00+00:00") == 1
    assert store.company_count() == 1
    assert store.snapshot_count() == 1

    changed = sample_dataframe()
    changed.loc[0, "company_rating"] = 4.5
    assert store.import_dataframe(changed, "2026-08-28T10:00:00+00:00") == 1
    assert store.company_count() == 1
    assert store.snapshot_count() == 2

    with store.connect() as connection:
        change = connection.execute(
            "SELECT field_name, old_value, new_value FROM change_log WHERE change_type='updated'"
        ).fetchone()

    assert tuple(change) == ("company_rating", "4.2", "4.5")


def test_sqlite_store_records_refresh_history(tmp_path):
    store = SQLiteStore(tmp_path / "ambitionbox.db")
    store.initialize()

    store.record_refresh_run({
        "snapshot_at": "2026-08-28T10:00:00+00:00",
        "previous_records": 64210,
        "incoming_records": 380,
        "final_records": 64588,
        "new_records": 380,
        "updated_records": 0,
        "duplicate_records": 2,
        "invalid_records": 0,
        "collapsed_records": 2,
        "applied": True,
        "source": "local",
    })

    assert store.refresh_run_count() == 1
    runs = store.list_refresh_runs()
    assert len(runs) == 1
    assert runs[0]["final_records"] == 64588
    assert runs[0]["duplicate_records"] == 2
