"""Refresh-health trend analytics for the AmbitionBox pipeline."""

from __future__ import annotations

from typing import Any


def summarize_health_runs(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Return compact trend metrics from refresh-run records."""
    if not rows:
        return {
            "runs": [],
            "latest": None,
            "healthy_runs": 0,
            "warning_runs": 0,
            "blocked_runs": 0,
            "average_score": None,
        }

    normalized = []
    for row in rows:
        score = row.get("health_score")
        status = row.get("health_status") or "unknown"
        normalized.append({
            **row,
            "health_score": None if score is None else int(score),
            "health_status": str(status),
        })

    scores = [r["health_score"] for r in normalized if r["health_score"] is not None]
    return {
        "runs": normalized,
        "latest": normalized[-1],
        "healthy_runs": sum(r["health_status"] == "healthy" for r in normalized),
        "warning_runs": sum(r["health_status"] == "warning" for r in normalized),
        "blocked_runs": sum(r["health_status"] == "blocked" for r in normalized),
        "average_score": round(sum(scores) / len(scores), 1) if scores else None,
    }
