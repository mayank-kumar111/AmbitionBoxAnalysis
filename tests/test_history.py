import pandas as pd

from src.analytics.history import HistoricalAnalytics
from src.database.sqlite_store import SQLiteStore


def _seed_db(path):
    store = SQLiteStore(path)
    store.initialize()
    first = pd.DataFrame([
        {"company_name": "Example Corp", "company_rating": 4.0, "industry": "IT", "size": "1k-5k Employees", "type": "Private", "years_old": 10, "location": "Jaipur"},
        {"company_name": "New Co", "company_rating": 3.5, "industry": "IT", "size": "1k-5k Employees", "type": "Startup", "years_old": 2, "location": "Delhi"},
    ])
    store.import_dataframe(first, "2026-08-27T10:00:00")
    second = first.copy()
    second.loc[0, "company_rating"] = 4.5
    store.import_dataframe(second, "2026-08-28T10:00:00")
    return path


def test_history_tracks_snapshots_and_rating_change(tmp_path):
    db = _seed_db(tmp_path / "test.db")
    analytics = HistoricalAnalytics(db)

    summary = analytics.snapshot_summary()
    changes = analytics.rating_changes()
    improved = analytics.most_improved_companies()

    assert len(summary) == 2
    assert len(changes) == 1
    assert changes.iloc[0]["old_rating"] == 4.0
    assert changes.iloc[0]["new_rating"] == 4.5
    assert improved.iloc[0]["company_name"] == "Example Corp"


def test_company_history_filters_by_location(tmp_path):
    db = _seed_db(tmp_path / "test.db")
    history = HistoricalAnalytics(db).company_history("Example Corp", "Jaipur")

    assert len(history) == 2
    assert history.iloc[-1]["company_rating"] == 4.5
