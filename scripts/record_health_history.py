"""Append the latest refresh health result to a local history JSON file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def record_health(report_path: str | Path, history_path: str | Path) -> list[dict]:
    report_file = Path(report_path)
    history_file = Path(history_path)
    report = json.loads(report_file.read_text(encoding="utf-8"))
    health = report.get("health", {})

    history = []
    if history_file.exists():
        try:
            history = json.loads(history_file.read_text(encoding="utf-8"))
            if not isinstance(history, list):
                history = []
        except json.JSONDecodeError:
            history = []

    entry = {
        "snapshot": report.get("snapshot"),
        "previous_records": report.get("previous_records", 0),
        "incoming_records": report.get("incoming_records", 0),
        "final_records": report.get("final_records", 0),
        "new_records": report.get("new_records", 0),
        "updated_records": report.get("updated_records", 0),
        "duplicate_records": report.get("duplicate_records", 0),
        "invalid_records": report.get("invalid_records", 0),
        "rating_changes": report.get("rating_changes", 0),
        "collapsed_records": report.get("collapsed_records", 0),
        "health_score": health.get("score"),
        "health_status": str(health.get("status", "Unknown")).lower(),
        "anomaly_count": health.get("anomaly_count", 0),
        "critical_count": health.get("critical_count", 0),
        "warning_count": health.get("warning_count", 0),
        "applied": bool(report.get("applied", False)),
    }

    history = [item for item in history if item.get("snapshot") != entry["snapshot"]]
    history.append(entry)
    history.sort(key=lambda item: item.get("snapshot") or "")
    history = history[-100:]

    history_file.parent.mkdir(parents=True, exist_ok=True)
    history_file.write_text(json.dumps(history, indent=2), encoding="utf-8")
    return history


def main() -> None:
    parser = argparse.ArgumentParser(description="Record refresh health history.")
    parser.add_argument("report", type=Path)
    parser.add_argument("--output", type=Path, default=Path("ambitionbox_app/static/refresh_health_history.json"))
    args = parser.parse_args()
    history = record_health(args.report, args.output)
    print(f"Recorded refresh health history: {len(history)} runs")


if __name__ == "__main__":
    main()
