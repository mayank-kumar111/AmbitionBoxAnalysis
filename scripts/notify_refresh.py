"""Send a refresh alert to Slack when a run is warning/blocked."""

from __future__ import annotations

import argparse
import json
import os
import urllib.request
from pathlib import Path


def build_message(report: dict) -> str | None:
    health = report.get("health") or {}
    status = str(health.get("status") or "").lower()
    if status not in {"warning", "blocked"}:
        return None

    alerts = report.get("alerts") or {}
    anomalies = report.get("anomalies") or []
    lines = [
        "AmbitionBox refresh alert",
        f"Status: {health.get('status', 'Unknown')}",
        f"Health score: {health.get('score', 'N/A')}/100",
        f"Snapshot: {report.get('snapshot', 'unknown')}",
        f"New: {report.get('new_records', 0)} | Updated: {report.get('updated_records', 0)} | Duplicates: {report.get('duplicate_records', 0)} | Rating changes: {report.get('rating_changes', 0)}",
    ]

    if anomalies:
        lines.append("Anomalies:")
        for item in anomalies[:8]:
            lines.append(
                f"- {str(item.get('severity', 'warning')).upper()}: {item.get('code', 'ANOMALY')} — {item.get('message', '')}"
            )
    elif alerts.get("alert_count"):
        lines.append(f"Alerts: {alerts.get('alert_count')}")

    if report.get("applied"):
        lines.append("Dataset update: applied")
    else:
        lines.append("Dataset update: not applied")
    return "\n".join(lines)


def send_slack(webhook_url: str, message: str) -> None:
    payload = json.dumps({"text": message}).encode("utf-8")
    request = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        if response.status < 200 or response.status >= 300:
            raise RuntimeError(f"Slack webhook returned HTTP {response.status}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Notify on AmbitionBox refresh warnings/blocking anomalies.")
    parser.add_argument("report", type=Path)
    parser.add_argument("--webhook", default=os.getenv("SLACK_WEBHOOK_URL"))
    args = parser.parse_args()

    report = json.loads(args.report.read_text(encoding="utf-8"))
    message = build_message(report)
    if not message:
        print("No warning or blocked notification required.")
        return
    if not args.webhook:
        print("Warning/blocked run detected, but SLACK_WEBHOOK_URL is not configured.")
        return
    send_slack(args.webhook, message)
    print("Refresh notification sent.")


if __name__ == "__main__":
    main()
