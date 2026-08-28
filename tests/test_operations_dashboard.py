import json
from pathlib import Path


def test_operations_dashboard_routes_exist(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    (report_dir / "update_report.json").write_text(
        json.dumps(
            {
                "health": {"status": "Healthy", "score": 100},
                "alerts": {"alert_count": 0},
                "final_records": 10,
                "new_records": 2,
                "updated_records": 1,
            }
        ),
        encoding="utf-8",
    )

    from ambitionbox_app import ops_routes

    # Patch module paths so the test does not depend on the real repository data.
    ops_routes.ROOT_DIR = Path(tmp_path)
    ops_routes.DATABASE_PATH = tmp_path / "data" / "ambitionbox.db"
    ops_routes.MASTER_PATH = tmp_path / "ambitionbox_app" / "data" / "companies.csv"
    ops_routes.REPORT_PATH = report_dir / "update_report.json"
    ops_routes.BACKUP_DIR = tmp_path / "data" / "backups" / "master"

    from flask import Flask

    app = Flask(__name__)
    ops_routes.register_ops_routes(app)
    client = app.test_client()

    assert client.get("/ops").status_code == 200
    response = client.get("/api/ops")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["latest_refresh"]["health"]["status"] == "Healthy"
    assert payload["latest_refresh"]["metrics"]["final_records"] == 10
