"""Cleaning and normalization for raw AmbitionBox company data."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

FINAL_COLUMNS = [
    "company_name",
    "company_rating",
    "industry",
    "size",
    "type",
    "years_old",
    "location",
]

# Observed company-type labels from the project dataset plus the original
# parser's supported labels. Values are matched case-insensitively.
TYPE_VALUES = {
    "public",
    "private",
    "government",
    "state",
    "central",
    "startup",
    "mnc",
    "partnership",
    "proprietorship",
    "conglomerate",
    "fortune india 500",
    "forbes global 2000",
    "indian unicorn",
}

SIZE_PATTERN = re.compile(r"\b(?:\d+(?:\.\d+)?[kKmM]?|1\s*Lakh\+?|50k-1\s*Lakh|10k-50k|5k-10k|1k-5k)\s*Employees(?:\s*\([^)]*\))?\b", re.I)
AGE_PATTERN = re.compile(r"\b(\d+)\s+years?\s+old\b", re.I)
MORE_PATTERN = re.compile(r"\s*\+\d+\s+more\s*$", re.I)


def _parts(value: object) -> list[str]:
    if pd.isna(value):
        return []
    text = re.sub(r"\s+", " ", str(value)).strip()
    if not text:
        return []
    return [part.strip(" ,") for part in text.split(",") if part.strip(" ,")]


def _find_size(parts: list[str]) -> tuple[str | None, int | None]:
    for index, part in enumerate(parts):
        if "employees" in part.lower():
            return part, index
    return None, None


def _find_age(parts: list[str]) -> tuple[int | None, int | None]:
    for index, part in enumerate(parts):
        match = AGE_PATTERN.search(part)
        if match:
            return int(match.group(1)), index
    return None, None


def _find_type(parts: list[str], excluded: set[int]) -> tuple[str | None, int | None]:
    for index, part in enumerate(parts):
        if index in excluded:
            continue
        if part.casefold() in TYPE_VALUES:
            return part, index
    return None, None


def parse_other_data(value: object) -> dict[str, object]:
    """Parse the semi-structured ``other_data`` field by content, not position."""
    parts = _parts(value)
    if not parts:
        return {"industry": None, "size": None, "type": None, "years_old": None, "location": None}

    location = MORE_PATTERN.sub("", parts[-1]).strip(" ,") or None
    size, size_index = _find_size(parts)
    years_old, age_index = _find_age(parts)

    excluded = {index for index in (size_index, age_index) if index is not None}
    company_type, type_index = _find_type(parts, excluded)
    if type_index is not None:
        excluded.add(type_index)

    location_index = len(parts) - 1
    excluded.add(location_index)
    industry_parts = [part for index, part in enumerate(parts) if index not in excluded]
    industry = ", ".join(industry_parts).strip(" ,") or None

    return {
        "industry": industry,
        "size": size,
        "type": company_type,
        "years_old": years_old,
        "location": location,
    }


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Convert raw company records into the canonical project schema."""
    required = {"company_name", "company_rating", "other_data"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    clean = df.drop(columns=[column for column in df.columns if column.lower().startswith("unnamed:")], errors="ignore").copy()
    clean["company_name"] = clean["company_name"].astype("string").str.strip()
    clean["company_name"] = clean["company_name"].replace({"": pd.NA, "nan": pd.NA})
    clean["company_rating"] = pd.to_numeric(clean["company_rating"], errors="coerce")

    parsed = clean["other_data"].apply(parse_other_data).apply(pd.Series)
    clean = pd.concat([clean.drop(columns=["other_data"]), parsed], axis=1)

    clean["years_old"] = pd.to_numeric(clean["years_old"], errors="coerce").astype("Int64")
    clean["company_rating"] = clean["company_rating"].where(clean["company_rating"].between(1, 5))

    for column in ["industry", "size", "type", "location"]:
        clean[column] = clean[column].astype("string").str.strip()
        clean[column] = clean[column].replace({"": pd.NA, "nan": pd.NA})

    clean = clean[FINAL_COLUMNS]
    clean = clean.drop_duplicates().reset_index(drop=True)
    return clean


def clean_csv(input_path: str | Path, output_path: str | Path) -> pd.DataFrame:
    """Read a raw CSV, clean it, and write the canonical CSV."""
    source = Path(input_path)
    destination = Path(output_path)
    df = pd.read_csv(source)
    clean = clean_dataframe(df)
    destination.parent.mkdir(parents=True, exist_ok=True)
    clean.to_csv(destination, index=False)
    return clean
