import sqlite3

from src.database.sqlite_store import SQLiteStore


def test_history_query_indexes_are_created(tmp_path):
    db_path = tmp_path / "ambitionbox.db"
    store = SQLiteStore(db_path)
    store.initialize()

    with sqlite3.connect(db_path) as connection:
        indexes = {
            row[1]
            for row in connection.execute("PRAGMA index_list('companies')").fetchall()
        }
        indexes |= {
            row[1]
            for row in connection.execute("PRAGMA index_list('company_snapshots')").fetchall()
        }
        indexes |= {
            row[1]
            for row in connection.execute("PRAGMA index_list('change_log')").fetchall()
        }

    assert "idx_companies_lower_name_location" in indexes
    assert "idx_snapshots_time_company" in indexes
    assert "idx_change_log_company_time" in indexes
