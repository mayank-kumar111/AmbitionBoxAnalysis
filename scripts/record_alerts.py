"""Persist the latest refresh alerts for the local dashboard."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Persist refresh alerts.")
    parser.add_argument("report", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    report = json.loads(args.report.read_text(encoding="utf-8"))
    health = report.get("health", {})
    anomalies = report.get("anomalies", []) or []
    payload = {
        "snapshot": report.get("snapshot"),
        "status": health.get("status", "Healthy"),
        "score": int(health.get("score", 100)),
        "alerts": [
            {
                "severity": item.get("severity", "warning"),
                "code": item.get("code", "UNKNOWN"),
                "message": item.get("message", "Refresh anomaly detected."),
                "metric": item.get("metric"),
                "value": item.get("value"),
                "threshold": item.get("threshold"),
            }
            for item in anomalies
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


if __name__ == "__main__":
    main()
