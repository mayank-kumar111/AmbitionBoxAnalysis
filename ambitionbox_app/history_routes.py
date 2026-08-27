"""History dashboard routes backed by the project's SQLite store."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from flask import jsonify, render_template


ROOT_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = ROOT_DIR / "data" / "ambitionbox.db"


def _connect():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def register_history_routes(app):
    @app.route("/history")
    def history():
        return render_template("history.html")

    @app.route("/api/history")
    def api_history():
        if not DATABASE_PATH.exists():
            return jsonify({
                "current_companies": 0,
                "snapshot_count": 0,
                "new_records": 0,
                "rating_updates": 0,
                "latest_snapshot": None,
                "growth": [],
                "latest_activity": [],
                "improved_companies": [],
                "latest_new": [],
            })

        with _connect() as db:
            current = db.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
            snapshots = db.execute("SELECT COUNT(*) FROM company_snapshots").fetchone()[0]
            new_records = db.execute(
                "SELECT COUNT(*) FROM change_log WHERE change_type='new'"
            ).fetchone()[0]
            rating_updates = db.execute(
                "SELECT COUNT(*) FROM change_log WHERE change_type='updated' AND field_name='company_rating'"
            ).fetchone()[0]

            growth_rows = db.execute("""
                SELECT snapshot_at, COUNT(DISTINCT company_id) AS companies
                FROM company_snapshots
                GROUP BY snapshot_at
                ORDER BY snapshot_at
            """).fetchall()

            activity_rows = db.execute("""
                SELECT snapshot_at, company_name, location, change_type, field_name,
                       old_value, new_value
                FROM change_log
                ORDER BY snapshot_at DESC, change_id DESC
                LIMIT 12
            """).fetchall()

            improved_rows = db.execute("""
                SELECT company_name, location,
                       SUM(CASE WHEN field_name='company_rating'
                                THEN CAST(new_value AS REAL) - CAST(old_value AS REAL)
                                ELSE 0 END) AS rating_change
                FROM change_log
                WHERE change_type='updated'
                  AND field_name='company_rating'
                  AND old_value IS NOT NULL
                  AND new_value IS NOT NULL
                GROUP BY company_name, location
                HAVING rating_change > 0
                ORDER BY rating_change DESC
                LIMIT 10
            """).fetchall()

            new_rows = db.execute("""
                SELECT company_name, location, snapshot_at
                FROM change_log
                WHERE change_type='new'
                ORDER BY snapshot_at DESC, change_id DESC
                LIMIT 10
            """).fetchall()

            latest_snapshot = db.execute(
                "SELECT MAX(snapshot_at) FROM company_snapshots"
            ).fetchone()[0]

        return jsonify({
            "current_companies": int(current),
            "snapshot_count": int(snapshots),
            "new_records": int(new_records),
            "rating_updates": int(rating_updates),
            "latest_snapshot": latest_snapshot,
            "growth": [dict(row) for row in growth_rows],
            "latest_activity": [dict(row) for row in activity_rows],
            "improved_companies": [
                {**dict(row), "change": round(float(row["rating_change"]), 2)}
                for row in improved_rows
            ],
            "latest_new": [dict(row) for row in new_rows],
        })
