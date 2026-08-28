"""SQLite persistence for company snapshots, refresh history, and change history."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

from src.preprocessing.cleaner import FINAL_COLUMNS


SCHEMA = """
CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    company_rating REAL,
    industry TEXT,
    size TEXT,
    type TEXT,
    years_old INTEGER,
    location TEXT,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    UNIQUE(company_name, location)
);

CREATE TABLE IF NOT EXISTS company_snapshots (
    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    snapshot_at TEXT NOT NULL,
    company_rating REAL,
    industry TEXT,
    size TEXT,
    type TEXT,
    years_old INTEGER,
    location TEXT,
    FOREIGN KEY(company_id) REFERENCES companies(id)
);

CREATE TABLE IF NOT EXISTS change_log (
    change_id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_at TEXT NOT NULL,
    company_id INTEGER,
    company_name TEXT NOT NULL,
    location TEXT,
    change_type TEXT NOT NULL,
    field_name TEXT,
    old_value TEXT,
    new_value TEXT,
    FOREIGN KEY(company_id) REFERENCES companies(id)
);

CREATE TABLE IF NOT EXISTS refresh_runs (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_at TEXT NOT NULL UNIQUE,
    previous_records INTEGER NOT NULL DEFAULT 0,
    incoming_records INTEGER NOT NULL DEFAULT 0,
    final_records INTEGER NOT NULL DEFAULT 0,
    new_records INTEGER NOT NULL DEFAULT 0,
    updated_records INTEGER NOT NULL DEFAULT 0,
    duplicate_records INTEGER NOT NULL DEFAULT 0,
    invalid_records INTEGER NOT NULL DEFAULT 0,
    collapsed_records INTEGER NOT NULL DEFAULT 0,
    applied INTEGER NOT NULL DEFAULT 0,
    source TEXT NOT NULL DEFAULT 'local'
);

CREATE INDEX IF NOT EXISTS idx_companies_name_location
    ON companies(company_name, location);
CREATE INDEX IF NOT EXISTS idx_companies_lower_name_location
    ON companies(lower(company_name), lower(location));
CREATE INDEX IF NOT EXISTS idx_snapshots_company_time
    ON company_snapshots(company_id, snapshot_at);
CREATE INDEX IF NOT EXISTS idx_snapshots_time_company
    ON company_snapshots(snapshot_at, company_id);
CREATE INDEX IF NOT EXISTS idx_change_log_time
    ON change_log(snapshot_at);
CREATE INDEX IF NOT EXISTS idx_change_log_company_time
    ON change_log(company_id, snapshot_at);
CREATE INDEX IF NOT EXISTS idx_refresh_runs_time
    ON refresh_runs(snapshot_at);
"""


class SQLiteStore:
    """Small persistence layer suitable for local development and prototypes."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(SCHEMA)

    def company_count(self) -> int:
        with self.connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM companies").fetchone()
            return int(row["count"])

    def snapshot_count(self) -> int:
        with self.connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM company_snapshots").fetchone()
            return int(row["count"])

    def refresh_run_count(self) -> int:
        with self.connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM refresh_runs").fetchone()
            return int(row["count"])

    def record_refresh_run(self, metrics: dict[str, Any]) -> None:
        """Persist one refresh-run summary for dashboard reporting."""
        snapshot_at = str(metrics.get("snapshot_at", "")).strip()
        if not snapshot_at:
            raise ValueError("snapshot_at is required for a refresh run")

        fields = [
            "snapshot_at", "previous_records", "incoming_records", "final_records",
            "new_records", "updated_records", "duplicate_records", "invalid_records",
            "collapsed_records", "applied", "source",
        ]
        values = [
            snapshot_at,
            int(metrics.get("previous_records", 0) or 0),
            int(metrics.get("incoming_records", 0) or 0),
            int(metrics.get("final_records", 0) or 0),
            int(metrics.get("new_records", 0) or 0),
            int(metrics.get("updated_records", 0) or 0),
            int(metrics.get("duplicate_records", metrics.get("incoming_duplicate_rows", 0)) or 0),
            int(metrics.get("invalid_records", 0) or 0),
            int(metrics.get("collapsed_records", 0) or 0),
            1 if metrics.get("applied", False) else 0,
            str(metrics.get("source", "local")),
        ]

        with self.connect() as connection:
            connection.execute(
                f"""INSERT OR REPLACE INTO refresh_runs ({', '.join(fields)})
                VALUES ({', '.join(['?'] * len(fields))})""",
                values,
            )

    def list_refresh_runs(self, limit: int = 30) -> list[dict[str, Any]]:
        limit = max(1, min(200, int(limit)))
        with self.connect() as connection:
            rows = connection.execute(
                """SELECT snapshot_at, previous_records, incoming_records, final_records,
                          new_records, updated_records, duplicate_records, invalid_records,
                          collapsed_records, applied, source
                   FROM refresh_runs
                   ORDER BY snapshot_at ASC
                   LIMIT ?""",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def import_dataframe(self, df: pd.DataFrame, snapshot_at: str) -> int:
        """Insert or update companies and record a snapshot for every row."""
        missing = set(FINAL_COLUMNS) - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")

        rows = df[FINAL_COLUMNS].to_dict(orient="records")
        inserted_or_updated = 0

        with self.connect() as connection:
            for row in rows:
                key = (str(row["company_name"]).strip(), str(row["location"]).strip())
                existing = connection.execute(
                    "SELECT * FROM companies WHERE company_name = ? AND location = ?",
                    key,
                ).fetchone()

                if existing is None:
                    cursor = connection.execute(
                        """INSERT INTO companies
                        (company_name, company_rating, industry, size, type, years_old,
                         location, first_seen, last_seen)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            key[0], row["company_rating"], row["industry"], row["size"],
                            row["type"], row["years_old"], key[1], snapshot_at, snapshot_at,
                        ),
                    )
                    company_id = int(cursor.lastrowid)
                    connection.execute(
                        """INSERT INTO change_log
                        (snapshot_at, company_id, company_name, location, change_type)
                        VALUES (?, ?, ?, ?, 'new')""",
                        (snapshot_at, company_id, key[0], key[1]),
                    )
                else:
                    company_id = int(existing["id"])
                    changed = []
                    for field in ["company_rating", "industry", "size", "type", "years_old"]:
                        old_value = existing[field]
                        new_value = row[field]
                        if not _same_value(old_value, new_value):
                            changed.append((field, old_value, new_value))

                    if changed:
                        connection.execute(
                            """UPDATE companies SET company_rating=?, industry=?, size=?,
                            type=?, years_old=?, last_seen=? WHERE id=?""",
                            (
                                row["company_rating"], row["industry"], row["size"],
                                row["type"], row["years_old"], snapshot_at, company_id,
                            ),
                        )
                        for field, old_value, new_value in changed:
                            connection.execute(
                                """INSERT INTO change_log
                                (snapshot_at, company_id, company_name, location,
                                 change_type, field_name, old_value, new_value)
                                VALUES (?, ?, ?, ?, 'updated', ?, ?, ?)""",
                                (
                                    snapshot_at, company_id, key[0], key[1], field,
                                    _stringify(old_value), _stringify(new_value),
                                ),
                            )
                    else:
                        connection.execute(
                            "UPDATE companies SET last_seen=? WHERE id=?",
                            (snapshot_at, company_id),
                        )

                connection.execute(
                    """INSERT INTO company_snapshots
                    (company_id, snapshot_at, company_rating, industry, size, type,
                     years_old, location)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        company_id, snapshot_at, row["company_rating"], row["industry"],
                        row["size"], row["type"], row["years_old"], key[1],
                    ),
                )
                inserted_or_updated += 1

        return inserted_or_updated


def _same_value(left: object, right: object) -> bool:
    if pd.isna(left) and pd.isna(right):
        return True
    if pd.isna(left) or pd.isna(right):
        return False
    return str(left).strip() == str(right).strip()


def _stringify(value: object) -> str | None:
    return None if pd.isna(value) else str(value)
