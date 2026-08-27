"""Generate a data-quality report for a cleaned AmbitionBox CSV."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow ``python scripts/data_quality.py ...`` to work from the repository root.
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd

from src.preprocessing.quality import profile_dataframe


def main() -> None:
    parser = argparse.ArgumentParser(description="Profile an AmbitionBox dataset.")
    parser.add_argument("input", type=Path, help="CSV to profile")
    parser.add_argument("--output", type=Path, default=Path("reports/data_quality.json"))
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    report = profile_dataframe(df)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Rows: {report['rows']:,}")
    print(f"Columns: {report['columns']:,}")
    print(f"Duplicates: {report['duplicate_rows']:,}")
    print(f"Invalid ratings: {report['invalid_rating_rows']:,}")
    print(f"Invalid ages: {report['invalid_age_rows']:,}")
    print(f"Status: {report['quality_status']}")
    print(f"Report: {args.output}")


if __name__ == "__main__":
    main()
