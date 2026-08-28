"""Small deterministic end-to-end test for the ingestion and history pipeline."""

from __future__ import annotations

import pandas as pd

from src.database.sqlite_store import SQLiteStore
from src.ingestion.incremental import IncrementalIngestor
from src.preprocessing.cleaner import clean_dataframe
from src.preprocessing.validator import validate_or_raise
from src.quality.anomaly_detector import detect_anomalies
from src.quality.health import summarize_health


def _raw_frame(count: int, *, updated_first: bool = False, include_new: bool = False) -> pd.DataFrame:
    rows = []
    for index in range(count):
        rating = 4.0 + (0.2 if updated_first and index == 0 else 0.0)
        rows.append({
            "company_name": f"Company {index}",
            "company_rating": str(rating),
            "other_data": "IT Services, 1k-5k Employees, Private, 10 years old, Jaipur +2 more",
        })
    if include_new:
        rows.append({
            "company_name": "New Company",
            "company_rating": "4.5",
            "other_data": "Finance, 201-500 Employees, Public, 5 years old, Pune",
        })
    return pd.DataFrame(rows)


def test_end_to_end_ingestion_to_sqlite_history(tmp_path):
    master_clean = clean_dataframe(_raw_frame(20))
    incoming_clean = clean_dataframe(_raw_frame(20, updated_first=True, include_new=True))

    validate_or_raise(master_clean)
    validate_or_raise(incoming_clean)

    master_path = tmp_path / "master.csv"
    output_path = tmp_path / "merged.csv"
    master_clean.to_csv(master_path, index=False)

    merged, result = IncrementalIngestor(master_path).merge(
        incoming_clean,
        output_path=output_path,
    )

    assert result.previous_records == 20
    assert result.incoming_records == 21
    assert result.new_records == 1
    assert result.updated_records == 1
    assert result.final_records == 21
    assert output_path.exists()
    assert len(merged) == 21

    database = tmp_path / "ambitionbox.db"
    store = SQLiteStore(database)
    store.initialize()
    store.import_dataframe(master_clean, "2026-08-28T10:00:00+00:00")
    store.import_dataframe(incoming_clean, "2026-08-28T11:00:00+00:00")
    store.record_refresh_run({
        "snapshot_at": "2026-08-28T11:00:00+00:00",
        **result.to_dict(),
        "duplicate_records": result.incoming_duplicate_rows + result.master_duplicate_keys,
        "applied": True,
        "source": "test",
    })

    assert store.company_count() == 21
    assert store.snapshot_count() == 41
    assert store.refresh_run_count() == 1

    with store.connect() as connection:
        row = connection.execute(
            """SELECT field_name, old_value, new_value
               FROM change_log
               WHERE change_type='updated' AND field_name='company_rating'"""
        ).fetchone()
    assert tuple(row) == ("company_rating", "4.0", "4.2")

    anomalies = detect_anomalies(
        previous_records=result.previous_records,
        incoming_records=result.incoming_records,
        final_records=result.final_records,
        new_records=result.new_records,
        updated_records=result.updated_records,
        duplicate_records=0,
        invalid_records=0,
        rating_changes=1,
    )
    assert anomalies == []

    health = summarize_health({"anomalies": [], "applied": True})
    assert health["score"] == 100
    assert health["status"] == "Healthy"
