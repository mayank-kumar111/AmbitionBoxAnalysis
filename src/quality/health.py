"""Refresh health scoring and human-readable status."""

from __future__ import annotations

from typing import Any


def health_score(anomalies: list[dict[str, Any]] | list[Any]) -> tuple[int, str]:
    """Convert anomaly severity into a 0-100 score and status."""
    score = 100
    has_warning = False
    for anomaly in anomalies:
        severity = getattr(anomaly, "severity", None) or anomaly.get("severity", "warning")
        if severity == "critical":
            score -= 60
        else:
            score -= 20
            has_warning = True
    score = max(0, score)
    if score < 60:
        status = "Blocked"
    elif has_warning or score < 90:
        status = "Warning"
    else:
        status = "Healthy"
    return score, status


def summarize_health(report: dict[str, Any]) -> dict[str, Any]:
    anomalies = report.get("anomalies", []) or []
    score, status = health_score(anomalies)
    return {
        "score": score,
        "status": status,
        "anomaly_count": len(anomalies),
        "critical_count": sum(1 for item in anomalies if item.get("severity") == "critical"),
        "warning_count": sum(1 for item in anomalies if item.get("severity") == "warning"),
        "applied": bool(report.get("applied", False)),
    }
