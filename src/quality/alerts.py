"""Build machine-readable alerts from refresh health/anomaly results."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def build_alerts(report: dict[str, Any]) -> list[dict[str, Any]]:
    """Return actionable alerts for warning/blocked refreshes."""
    health = report.get("health") or {}
    status = str(health.get("status", "Healthy"))
    anomalies = report.get("anomalies", []) or []
    if status == "Healthy" and not anomalies:
        return []

    alerts: list[dict[str, Any]] = []
    for anomaly in anomalies:
        severity = str(anomaly.get("severity", "warning")).lower()
        alerts.append({
            "created_at": datetime.now(timezone.utc).isoformat(),
            "severity": severity,
            "code": anomaly.get("code", "UNKNOWN"),
            "message": anomaly.get("message", "Refresh anomaly detected."),
            "metric": anomaly.get("metric"),
            "value": anomaly.get("value"),
            "threshold": anomaly.get("threshold"),
            "snapshot": report.get("snapshot"),
            "applied": bool(report.get("applied", False)),
        })
    return alerts


def alert_summary(report: dict[str, Any]) -> dict[str, Any]:
    health = report.get("health") or {}
    alerts = build_alerts(report)
    return {
        "status": health.get("status", "Healthy"),
        "score": int(health.get("score", 100)),
        "alert_count": len(alerts),
        "critical_count": sum(1 for item in alerts if item["severity"] == "critical"),
        "warning_count": sum(1 for item in alerts if item["severity"] == "warning"),
        "alerts": alerts,
    }
