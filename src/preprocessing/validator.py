"""Data-quality validation for the cleaned AmbitionBox dataset."""

from __future__ import annotations

import pandas as pd

from .cleaner import FINAL_COLUMNS


def validate_dataframe(df: pd.DataFrame) -> list[str]:
    """Return validation errors; an empty list means the frame is valid."""
    errors: list[str] = []

    missing_columns = [column for column in FINAL_COLUMNS if column not in df.columns]
    if missing_columns:
        return [f"Missing columns: {missing_columns}"]

    if df["company_name"].isna().any():
        errors.append("company_name contains missing values")

    invalid_ratings = df["company_rating"].dropna().loc[lambda s: ~s.between(1, 5)]
    if not invalid_ratings.empty:
        errors.append("company_rating contains values outside 1-5")

    invalid_ages = df["years_old"].dropna().loc[lambda s: s < 0]
    if not invalid_ages.empty:
        errors.append("years_old contains negative values")

    if df.duplicated().any():
        errors.append("dataset contains exact duplicate rows")

    return errors


def validate_or_raise(df: pd.DataFrame) -> None:
    """Raise ValueError when the cleaned dataframe fails validation."""
    errors = validate_dataframe(df)
    if errors:
        raise ValueError("Data validation failed: " + "; ".join(errors))
