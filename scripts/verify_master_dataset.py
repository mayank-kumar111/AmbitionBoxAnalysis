"""Post-refresh validation for the master company CSV."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.preprocessing.cleaner import FINAL_COLUMNS
from src.preprocessing.validator import validate_dataframe


def verify_master(path: str | Path, *, minimum_rows: int = 1) -> dict[str, object]:
    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Master dataset not found: {csv_path}")

    df = pd.read_csv(csv_path)
    errors = validate_dataframe(df, check_duplicates=False)
    missing = [column for column in FINAL_COLUMNS if column not in df.columns]
    if missing:
        errors.append(f"Missing columns: {missing}")

    if len(df) < minimum_rows:
        errors.append(f"Dataset contains {len(df)} rows; minimum is {minimum_rows}")

    duplicate_keys = 0
    if set(["company_name", "location"]).issubset(df.columns):
        duplicate_keys = int(df.duplicated(subset=["company_name", "location"], keep=False).sum())
        if duplicate_keys:
            errors.append("dataset contains duplicate company_name + location keys")

    ratings = pd.to_numeric(df["company_rating"], errors="coerce") if "company_rating" in df else pd.Series(dtype=float)
    invalid_rating_values = int((ratings.dropna().lt(1) | ratings.dropna().gt(5)).sum())

    report = {
        "path": str(csv_path),
        "rows": int(len(df)),
        "columns": list(df.columns),
        "minimum_rows": int(minimum_rows),
        "duplicate_keys": duplicate_keys,
        "invalid_rating_values": invalid_rating_values,
        "valid": not errors,
        "errors": errors,
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--master", default="ambitionbox_app/data/companies.csv")
    parser.add_argument("--minimum-rows", type=int, default=1)
    args = parser.parse_args()

    report = verify_master(args.master, minimum_rows=args.minimum_rows)
    print(f"Master dataset: {'VALID' if report['valid'] else 'INVALID'}")
    print(f"Rows: {report['rows']}")
    print(f"Duplicate keys: {report['duplicate_keys']}")
    print(f"Invalid ratings: {report['invalid_rating_values']}")
    for error in report["errors"]:
        print(f"ERROR: {error}")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
