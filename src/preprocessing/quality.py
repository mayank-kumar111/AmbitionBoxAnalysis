"""Data-quality profiling and validation reports."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pandas as pd

from .cleaner import FINAL_COLUMNS, TYPE_VALUES


DEFAULT_CATEGORICAL_COLUMNS = ["industry", "size", "type", "location"]


def profile_dataframe(
    df: pd.DataFrame,
    categorical_columns: Iterable[str] = DEFAULT_CATEGORICAL_COLUMNS,
) -> dict[str, Any]:
    """Build a JSON-serializable data-quality profile without modifying the data."""
    categorical_columns = [c for c in categorical_columns if c in df.columns]

    missing = df.isna().sum()
    duplicate_count = int(df.duplicated().sum())

    invalid_rating_count = 0
    if "company_rating" in df.columns:
        ratings = pd.to_numeric(df["company_rating"], errors="coerce")
        invalid_rating_count = int((ratings.notna() & ~ratings.between(1, 5)).sum())

    invalid_age_count = 0
    if "years_old" in df.columns:
        ages = pd.to_numeric(df["years_old"], errors="coerce")
        invalid_age_count = int((ages.notna() & (ages < 0)).sum())

    unknown_types = []
    if "type" in df.columns:
        values = df["type"].dropna().astype(str).str.strip()
        unknown_types = sorted(
            {value for value in values if value.casefold() not in TYPE_VALUES}
        )

    categorical_summary = {
        column: {
            "unique_values": int(df[column].dropna().nunique()),
            "missing_values": int(df[column].isna().sum()),
            "top_values": {
                str(key): int(value)
                for key, value in df[column].dropna().value_counts().head(10).items()
            },
        }
        for column in categorical_columns
    }

    return {
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "column_names": [str(column) for column in df.columns],
        "expected_columns": FINAL_COLUMNS,
        "missing_values": {str(key): int(value) for key, value in missing.items()},
        "missing_percent": {
            str(key): round(float(value / len(df) * 100), 2) if len(df) else 0.0
            for key, value in missing.items()
        },
        "duplicate_rows": duplicate_count,
        "invalid_rating_rows": invalid_rating_count,
        "invalid_age_rows": invalid_age_count,
        "unknown_company_types": unknown_types,
        "categorical_summary": categorical_summary,
        "quality_status": "PASS"
        if not (invalid_rating_count or invalid_age_count or unknown_types or duplicate_count)
        else "REVIEW",
    }
