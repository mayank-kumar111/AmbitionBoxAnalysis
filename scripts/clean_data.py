"""CLI for converting raw AmbitionBox CSV data to the canonical schema."""

import argparse
from pathlib import Path

from src.preprocessing.cleaner import clean_csv
from src.preprocessing.validator import validate_or_raise


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean an AmbitionBox CSV file.")
    parser.add_argument("input", type=Path, help="Path to the raw CSV")
    parser.add_argument("output", type=Path, help="Path for the cleaned CSV")
    args = parser.parse_args()

    cleaned = clean_csv(args.input, args.output)
    validate_or_raise(cleaned)
    print(f"Cleaned {len(cleaned):,} rows -> {args.output}")


if __name__ == "__main__":
    main()
