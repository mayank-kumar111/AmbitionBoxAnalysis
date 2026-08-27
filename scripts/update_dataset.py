"""Incrementally update a master company snapshot from incoming CSV files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.ingestion.incremental import IncrementalIngestor
from src.preprocessing.cleaner import FINAL_COLUMNS, clean_dataframe
from src.preprocessing.validator import validate_or_raise


def load_snapshot_files(directory: Path) -> pd.DataFrame:
    files = sorted(directory.glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"No CSV files found in {directory}")

    frames: list[pd.DataFrame] = []
    for path in files:
        frame = pd.read_csv(path)
        if "other_data" in frame.columns:
            frame = clean_dataframe(frame)
        else:
            missing = set(FINAL_COLUMNS) - set(frame.columns)
            if missing:
                raise ValueError(f"{path}: missing required columns: {sorted(missing)}")
            frame = frame[FINAL_COLUMNS]
        frames.append(frame)

    return pd.concat(frames, ignore_index=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Incrementally update the company dataset.")
    parser.add_argument("--incoming", type=Path, required=True, help="Directory containing new CSV snapshots")
    parser.add_argument("--master", type=Path, required=True, help="Current master CSV")
    parser.add_argument("--output", type=Path, required=True, help="Merged output CSV")
    parser.add_argument("--report", type=Path, default=Path("reports/update_report.json"))
    parser.add_argument("--apply", action="store_true", help="Write the merged dataset; otherwise dry-run")
    parser.add_argument("--full-snapshot", action="store_true", help="Treat incoming data as complete source coverage and report removals")
    args = parser.parse_args()

    incoming = load_snapshot_files(args.incoming)
    validate_or_raise(incoming)

    ingestor = IncrementalIngestor(args.master)
    merged, result = ingestor.merge(
        incoming,
        output_path=args.output if args.apply else None,
        full_snapshot=args.full_snapshot,
    )

    report = result.to_dict()
    report["new_companies"] = list(result.new_companies)
    report["updated_companies"] = list(result.updated_companies)
    report["applied"] = args.apply
    report["full_snapshot"] = args.full_snapshot

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    print(json.dumps(report, indent=2, default=str))
    if not args.apply:
        print("DRY RUN: no master dataset was changed. Use --apply to write the output.")
    else:
        print(f"Merged dataset written to: {args.output}")


if __name__ == "__main__":
    main()
