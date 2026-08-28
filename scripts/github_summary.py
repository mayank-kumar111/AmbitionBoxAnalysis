"""Write a concise GitHub Actions step summary from an update report."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    args = parser.parse_args()

    report = json.loads(args.report.read_text(encoding="utf-8"))
    health = report.get("health", {})
    anomalies = report.get("anomalies", []) or []

    lines = [
        "# AmbitionBox Data Refresh",
        "",
        f"**Status:** {health.get('status', 'Unknown')}  ",
        f"**Health score:** {health.get('score', '—')}/100  ",
        f"**Snapshot:** `{report.get('snapshot', '—')}`",
        "",
        "| Metric | Count |",
        "|---|---:|",
        f"| Previous records | {report.get('previous_records', 0):,} |",
        f"| Incoming records | {report.get('incoming_records', 0):,} |",
        f"| Final records | {report.get('final_records', 0):,} |",
        f"| New companies | {report.get('new_records', 0):,} |",
        f"| Updated companies | {report.get('updated_records', 0):,} |",
        f"| Duplicates | {report.get('duplicate_records', 0):,} |",
        f"| Rating changes | {report.get('rating_changes', 0):,} |",
        f"| Invalid records | {report.get('invalid_records', 0):,} |",
        "",
    ]

    if anomalies:
        lines += ["## Anomalies", ""]
        for item in anomalies:
            lines.append(
                f"- **{str(item.get('severity', 'warning')).upper()}** "
                f"`{item.get('code', 'ANOMALY')}` — {item.get('message', '')}"
            )
    else:
        lines += ["## Anomalies", "", "No anomalies detected."]

    output = os.environ.get("GITHUB_STEP_SUMMARY")
    if output:
        with open(output, "a", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")
    else:
        print("\n".join(lines))


if __name__ == "__main__":
    main()
