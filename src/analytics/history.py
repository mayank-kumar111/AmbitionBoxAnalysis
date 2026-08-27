"""Historical company analytics backed by the SQLite snapshot store."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


class HistoricalAnalytics:
    """Read-only analytics for company snapshots and the change log."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        if not self.database_path.exists():
            raise FileNotFoundError(f"Database not found: {self.database_path}")

    def _read_sql(self, query: str, params: tuple = ()) -> pd.DataFrame:
        with sqlite3.connect(self.database_path) as connection:
            return pd.read_sql_query(query, connection, params=params)

    def snapshot_summary(self) -> pd.DataFrame:
        return self._read_sql(
            """SELECT snapshot_at,
                      COUNT(*) AS companies_observed,
                      ROUND(AVG(company_rating), 3) AS average_rating
               FROM company_snapshots
               GROUP BY snapshot_at
               ORDER BY snapshot_at"""
        )

    def latest_changes(self, limit: int = 50) -> pd.DataFrame:
        return self._read_sql(
            """SELECT snapshot_at, company_name, location, change_type,
                      field_name, old_value, new_value
               FROM change_log
               ORDER BY change_id DESC
               LIMIT ?""",
            (limit,),
        )

    def rating_changes(self, limit: int = 50) -> pd.DataFrame:
        """Return the largest positive and negative rating changes."""
        return self._read_sql(
            """WITH ranked AS (
                   SELECT company_name,
                          location,
                          snapshot_at,
                          CAST(old_value AS REAL) AS old_rating,
                          CAST(new_value AS REAL) AS new_rating,
                          CAST(new_value AS REAL) - CAST(old_value AS REAL) AS rating_change
                   FROM change_log
                   WHERE change_type = 'updated'
                     AND field_name = 'company_rating'
                     AND old_value IS NOT NULL
                     AND new_value IS NOT NULL
               )
               SELECT *
               FROM ranked
               WHERE rating_change != 0
               ORDER BY ABS(rating_change) DESC, snapshot_at DESC
               LIMIT ?""",
            (limit,),
        )

    def new_companies(self, limit: int = 50) -> pd.DataFrame:
        return self._read_sql(
            """SELECT snapshot_at, company_name, location
               FROM change_log
               WHERE change_type = 'new'
               ORDER BY change_id DESC
               LIMIT ?""",
            (limit,),
        )

    def most_improved_companies(self, limit: int = 20) -> pd.DataFrame:
        """Aggregate positive rating changes by company."""
        return self._read_sql(
            """SELECT company_name,
                      location,
                      ROUND(SUM(CAST(new_value AS REAL) - CAST(old_value AS REAL)), 3) AS total_rating_gain,
                      COUNT(*) AS rating_updates
               FROM change_log
               WHERE change_type = 'updated'
                 AND field_name = 'company_rating'
                 AND old_value IS NOT NULL
                 AND new_value IS NOT NULL
                 AND CAST(new_value AS REAL) > CAST(old_value AS REAL)
               GROUP BY company_name, location
               ORDER BY total_rating_gain DESC, rating_updates DESC
               LIMIT ?""",
            (limit,),
        )

    def company_history(self, company_name: str, location: str | None = None) -> pd.DataFrame:
        query = """SELECT c.company_name, c.location, s.snapshot_at,
                         s.company_rating, s.industry, s.size, s.type, s.years_old
                  FROM company_snapshots s
                  JOIN companies c ON c.id = s.company_id
                  WHERE LOWER(c.company_name) = LOWER(?)"""
        params: list[str] = [company_name]
        if location:
            query += " AND LOWER(c.location) = LOWER(?)"
            params.append(location)
        query += " ORDER BY s.snapshot_at"
        return self._read_sql(query, tuple(params))
