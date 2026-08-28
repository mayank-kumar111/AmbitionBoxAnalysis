"""Data Operations dashboard routes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from flask import jsonify, render_template

from src.database.sqlite_store import SQLiteStore


ROOT_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = ROOT_DIR / "data" / "ambitionbox.db"
MASTER_PATH = ROOT_DIR / "ambitionbox_app" / "data" / "companies.csv"
REPORT_PATH = ROOT_DIR / "reports" / "update_report.json"
BACKUP_DIR = ROOT_DIR / "data" / "backups" / "master"


def _read_report() -> dict[str, Any]:
    if not REPORT_PATH.exists():
        return {}
    try:
        payload = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def register_ops_routes(app) -> None:
    @app.route("/ops")
    def operations():
        return render_template("operations.html")

    @app.route("/api/ops")
    def api_operations():
        report = _read_report()
        database_exists = DATABASE_PATH.exists()
        master_exists = MASTER_PATH.exists()

        db_payload = {
            "exists": database_exists,
            "companies": 0,
            "snapshots": 0,
            "refresh_runs": 0,
            "latest_snapshot": None,
        }
        if database_exists:
            try:
                store = SQLiteStore(DATABASE_PATH)
                recent_runs = store.list_refresh_runs(limit=1)
                db_payload.update(
                    {
                        "companies": store.company_count(),
                        "snapshots": store.snapshot_count(),
                        "refresh_runs": store.refresh_run_count(),
                        "latest_snapshot": recent_runs[0]["snapshot_at"] if recent_runs else None,
                    }
                )
            except Exception as exc:  # pragma: no cover - API safety boundary
                db_payload["error"] = str(exc)

        backups = []
        if BACKUP_DIR.exists():
            try:
                backups = sorted(
                    (
                        {"name": path.name, "size": path.stat().st_size}
                        for path in BACKUP_DIR.glob("companies-*.csv")
                        if path.is_file()
                    ),
                    key=lambda item: item["name"],
                    reverse=True,
                )[:10]
            except OSError:
                backups = []

        health = report.get("health") or {}
        alerts = report.get("alerts") or {}
        return jsonify(
            {
                "master": {
                    "exists": master_exists,
                    "size": MASTER_PATH.stat().st_size if master_exists else 0,
                    "modified_at": MASTER_PATH.stat().st_mtime if master_exists else None,
                },
                "database": db_payload,
                "latest_refresh": {
                    "health": health,
                    "alerts": alerts,
                    "metrics": {
                        key: report.get(key)
                        for key in (
                            "previous_records",
                            "incoming_records",
                            "final_records",
                            "new_records",
                            "updated_records",
                            "duplicate_records",
                            "invalid_records",
                            "rating_changes",
                            "applied",
                        )
                        if key in report
                    },
                },
                "backups": backups,
            }
        )
