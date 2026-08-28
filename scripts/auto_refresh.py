"""One-command automated AmbitionBox refresh for local Windows use.

Examples:
  python scripts/auto_refresh.py --pages 1 --apply
  python scripts/auto_refresh.py --extended --pages 2 --apply

The default is a dry run, so the master CSV is never changed unless --apply
is provided.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
COLLECT_SCRIPT = ROOT_DIR / "scripts" / "collect_and_update.py"


def main() -> int:
    parser = argparse.ArgumentParser(description="Automatically scrape and update AmbitionBox data.")
    parser.add_argument("--pages", type=int, default=1, help="Pages per location")
    parser.add_argument("--extended", action="store_true", help="Use all extended locations")
    parser.add_argument("--apply", action="store_true", help="Apply the merged dataset")
    parser.add_argument("--full-snapshot", action="store_true", help="Treat the collection as complete for removal checks")
    args = parser.parse_args()

    if args.pages < 1:
        parser.error("--pages must be at least 1")

    command = [
        sys.executable,
        str(COLLECT_SCRIPT),
        "--master", str(ROOT_DIR / "ambitionbox_app" / "data" / "companies.csv"),
        "--output", str(ROOT_DIR / "data" / "processed" / "companies_updated.csv"),
        "--report", str(ROOT_DIR / "reports" / "update_report.json"),
        "--pages", str(args.pages),
    ]
    if args.extended:
        command.append("--extended")
    if args.apply:
        command.append("--apply")
    if args.full_snapshot:
        command.append("--full-snapshot")

    print("Running:", " ".join(f'"{part}"' if " " in part else part for part in command))
    result = subprocess.run(command, cwd=ROOT_DIR)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
