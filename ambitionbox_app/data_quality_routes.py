"""Dashboard endpoint for the latest ingestion/data-quality summary."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from flask import jsonify

ROOT_DIR = Path(__file__).resolve().parent.parent
REPORT_PATH = ROOT_DIR / "reports" / "update_report.json"
DATABASE_PATH = ROOT_DIR / "data" / "ambitionbox.db"


def _read_report() -> dict | None:
    if not REPORT_PATH.exists():
        return None
    try:
        value = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _report_summary(report: dict | None) -> dict:
    if not report:
        return {
            "source": "none",
            "available": False,
            "snapshot": None,
            "previous_records": 0,
            "incoming_records": 0,
            "new_records": 0,
            "updated_records": 0,
            "unchanged_records": 0,
            "duplicate_records": 0,
            "collapsed_records": 0,
            "invalid_records": 0,
            "rating_changes": 0,
            "applied": False,
        }

    rating_changes = 0
    for item in report.get("updated_companies", []):
        if isinstance(item, dict) and "company_rating" in item.get("changes", {}):
            rating_changes += 1

    return {
        "source": "update_report",
        "available": True,
        "snapshot": report.get("snapshot"),
        "previous_records": int(report.get("previous_records", 0) or 0),
        "incoming_records": int(report.get("incoming_records", 0) or 0),
        "new_records": int(report.get("new_records", 0) or 0),
        "updated_records": int(report.get("updated_records", 0) or 0),
        "unchanged_records": int(report.get("unchanged_records", 0) or 0),
        "duplicate_records": int(report.get("incoming_duplicate_rows", 0) or 0),
        "collapsed_records": int(report.get("collapsed_records", 0) or 0),
        "invalid_records": int(report.get("invalid_records", 0) or 0),
        "rating_changes": rating_changes,
        "applied": bool(report.get("applied", False)),
    }


def _database_fallback() -> dict:
    result = _report_summary(None)
    result["source"] = "sqlite"
    result["available"] = DATABASE_PATH.exists()
    if not DATABASE_PATH.exists():
        return result

    with sqlite3.connect(DATABASE_PATH) as db:
        latest = db.execute("SELECT MAX(snapshot_at) FROM company_snapshots").fetchone()[0]
        result["snapshot"] = latest
        if latest:
            result["new_records"] = int(db.execute(
                "SELECT COUNT(*) FROM change_log WHERE snapshot_at=? AND change_type='new'", (latest,)
            ).fetchone()[0])
            result["updated_records"] = int(db.execute(
                "SELECT COUNT(DISTINCT company_id) FROM change_log WHERE snapshot_at=? AND change_type='updated'", (latest,)
            ).fetchone()[0])
            result["rating_changes"] = int(db.execute(
                "SELECT COUNT(*) FROM change_log WHERE snapshot_at=? AND change_type='updated' AND field_name='company_rating'", (latest,)
            ).fetchone()[0])
    return result


def register_data_quality_routes(app):
    @app.route("/api/data-quality")
    def api_data_quality():
        report = _report_summary(_read_report())
        if report["available"]:
            return jsonify(report)
        return jsonify(_database_fallback())
