import sqlite3

from flask import Flask

from ambitionbox_app.history_routes import register_history_routes
import ambitionbox_app.history_routes as history_routes


def _make_db(path):
    connection = sqlite3.connect(path)
    connection.executescript("""
    CREATE TABLE companies (
        id INTEGER PRIMARY KEY, company_name TEXT, company_rating REAL,
        industry TEXT, size TEXT, type TEXT, years_old INTEGER,
        location TEXT, first_seen TEXT, last_seen TEXT
    );
    CREATE TABLE company_snapshots (
        snapshot_id INTEGER PRIMARY KEY, company_id INTEGER, snapshot_at TEXT,
        company_rating REAL, industry TEXT, size TEXT, type TEXT,
        years_old INTEGER, location TEXT
    );
    CREATE TABLE change_log (
        change_id INTEGER PRIMARY KEY, snapshot_at TEXT, company_id INTEGER,
        company_name TEXT, location TEXT, change_type TEXT, field_name TEXT,
        old_value TEXT, new_value TEXT
    );
    INSERT INTO companies VALUES (1, 'Example Corp', 4.5, 'IT', '1k-5k', 'Private', 10, 'Jaipur', '2026-01-01', '2026-01-02');
    INSERT INTO company_snapshots VALUES (1, 1, '2026-01-01', 4.2, 'IT', '1k-5k', 'Private', 10, 'Jaipur');
    INSERT INTO company_snapshots VALUES (2, 1, '2026-01-02', 4.5, 'IT', '1k-5k', 'Private', 10, 'Jaipur');
    INSERT INTO change_log VALUES (1, '2026-01-01', 1, 'Example Corp', 'Jaipur', 'new', NULL, NULL, NULL);
    INSERT INTO change_log VALUES (2, '2026-01-02', 1, 'Example Corp', 'Jaipur', 'updated', 'company_rating', '4.2', '4.5');
    """)
    connection.commit()
    connection.close()


def _app():
    app = Flask(__name__, template_folder="../ambitionbox_app/templates")

    # The real application already defines these endpoints. They are supplied
    # here so the shared base template can render in this isolated route test.
    for endpoint in ("index", "explore", "dashboard", "compare", "about"):
        app.add_url_rule(f"/__test_{endpoint}", endpoint, lambda endpoint=endpoint: endpoint)

    register_history_routes(app)
    return app


def test_history_api_reads_sqlite(tmp_path, monkeypatch):
    db_path = tmp_path / "history.db"
    _make_db(db_path)
    monkeypatch.setattr(history_routes, "DATABASE_PATH", db_path)

    client = _app().test_client()
    response = client.get("/api/history")
    assert response.status_code == 200
    data = response.get_json()
    assert data["current_companies"] == 1
    assert data["snapshot_count"] == 2
    assert data["new_records"] == 1
    assert data["rating_updates"] == 1
    assert data["improved_companies"][0]["change"] == 0.3


def test_history_page_exists(tmp_path, monkeypatch):
    monkeypatch.setattr(history_routes, "DATABASE_PATH", tmp_path / "missing.db")
    response = _app().test_client().get("/history")
    assert response.status_code == 200
    assert b"Data history" in response.data
