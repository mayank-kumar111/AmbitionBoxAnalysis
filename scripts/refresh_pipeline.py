"""Run the safe AmbitionBox refresh pipeline end to end."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
MASTER = ROOT_DIR / "ambitionbox_app" / "data" / "companies.csv"
DATABASE = ROOT_DIR / "data" / "ambitionbox.db"
REPORT = ROOT_DIR / "reports" / "update_report.json"


def run(command: list[str]) -> int:
    return subprocess.run(command, cwd=ROOT_DIR).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the complete safe data refresh pipeline.")
    parser.add_argument("--pages", type=int, default=1)
    parser.add_argument("--extended", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--full-snapshot", action="store_true")
    args = parser.parse_args()

    if not 1 <= args.pages <= 10:
        parser.error("--pages must be between 1 and 10")

    master_backup = None
    if args.apply and MASTER.exists():
        backup_dir = ROOT_DIR / "data" / "backups" / "master"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_name = datetime.now(timezone.utc).strftime("companies-%Y%m%dT%H%M%SZ.csv")
        master_backup = backup_dir / backup_name
        code = run([
            sys.executable,
            str(ROOT_DIR / "scripts" / "master_backup.py"),
            "--master", str(MASTER),
            "--backup-dir", str(backup_dir),
        ])
        if code != 0:
            return code

    command = [
        sys.executable,
        str(ROOT_DIR / "scripts" / "auto_refresh.py"),
        "--pages", str(args.pages),
    ]
    if args.extended:
        command.append("--extended")
    if args.apply:
        command.append("--apply")
    if args.full_snapshot:
        command.append("--full-snapshot")

    code = run(command)
    if code != 0:
        return code

    if not args.apply:
        return 0

    code = run([
        sys.executable,
        str(ROOT_DIR / "scripts" / "verify_master_dataset.py"),
        "--master", str(MASTER),
    ])
    if code != 0:
        if master_backup and master_backup.exists():
            shutil.copy2(master_backup, MASTER)
        return 3

    try:
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        incoming = ROOT_DIR / str(report["incoming_directory"])
    except (OSError, KeyError, TypeError, json.JSONDecodeError):
        if master_backup and master_backup.exists():
            shutil.copy2(master_backup, MASTER)
        return 4

    code = run([
        sys.executable,
        str(ROOT_DIR / "scripts" / "refresh_history.py"),
        "--master", str(MASTER),
        "--incoming", str(incoming),
        "--database", str(DATABASE),
        "--report", str(ROOT_DIR / "reports" / "history_refresh.json"),
        "--update-report", str(REPORT),
    ])
    if code != 0:
        return code

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
