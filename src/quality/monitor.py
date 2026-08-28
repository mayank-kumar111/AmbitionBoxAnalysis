"""Refresh-health trend analytics for the AmbitionBox pipeline."""

from __future__ import annotations

from typing import Any


def summarize_health_runs(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Return compact trend metrics from refresh-run records.

    Status values are normalized case-insensitively so historical reports can use
    ``Healthy``/``Warning``/``Blocked`` or their lowercase equivalents.
    """
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
        raw_status = row.get("health_status") or "unknown"
        status = str(raw_status).strip()
        normalized.append({
            **row,
            "health_score": None if score is None else int(score),
            "health_status": status,
        })

    scores = [r["health_score"] for r in normalized if r["health_score"] is not None]
    status_counts = [r["health_status"].casefold() for r in normalized]

    return {
        "runs": normalized,
        "latest": normalized[-1],
        "healthy_runs": status_counts.count("healthy"),
        "warning_runs": status_counts.count("warning"),
        "blocked_runs": status_counts.count("blocked"),
        "average_score": round(sum(scores) / len(scores), 1) if scores else None,
    }
