"""Detect suspicious dataset refreshes before they affect analytics."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class Anomaly:
    code: str
    severity: str
    message: str
    metric: str
    value: float
    threshold: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def detect_anomalies(
    *,
    previous_records: int,
    incoming_records: int,
    final_records: int,
    new_records: int,
    updated_records: int,
    duplicate_records: int,
    invalid_records: int,
    rating_changes: int = 0,
    removed_records: int | None = None,
    max_growth_ratio: float = 0.25,
    max_drop_ratio: float = 0.10,
    max_duplicate_ratio: float = 0.05,
    max_invalid_ratio: float = 0.02,
    max_rating_change_ratio: float = 0.10,
) -> list[Anomaly]:
    """Return suspicious refresh conditions without blocking the run."""
    anomalies: list[Anomaly] = []
    baseline = max(previous_records, 1)
    incoming = max(incoming_records, 1)

    growth_ratio = (final_records - previous_records) / baseline
    if growth_ratio > max_growth_ratio:
        anomalies.append(Anomaly(
            "LARGE_DATASET_GROWTH", "warning",
            f"Dataset grew by {growth_ratio:.1%}, above the {max_growth_ratio:.1%} threshold.",
            "growth_ratio", growth_ratio, max_growth_ratio,
        ))

    if removed_records is not None:
        drop_ratio = removed_records / baseline
        if drop_ratio > max_drop_ratio:
            anomalies.append(Anomaly(
                "LARGE_DATASET_DROP", "critical",
                f"Dataset dropped by {drop_ratio:.1%}, above the {max_drop_ratio:.1%} threshold.",
                "drop_ratio", drop_ratio, max_drop_ratio,
            ))

    duplicate_ratio = duplicate_records / incoming
    if duplicate_ratio > max_duplicate_ratio:
        anomalies.append(Anomaly(
            "DUPLICATE_SPIKE", "warning",
            f"Incoming duplicate rate is {duplicate_ratio:.1%}, above {max_duplicate_ratio:.1%}.",
            "duplicate_ratio", duplicate_ratio, max_duplicate_ratio,
        ))

    invalid_ratio = invalid_records / incoming
    if invalid_ratio > max_invalid_ratio:
        anomalies.append(Anomaly(
            "INVALID_RECORD_SPIKE", "critical",
            f"Incoming invalid rate is {invalid_ratio:.1%}, above {max_invalid_ratio:.1%}.",
            "invalid_ratio", invalid_ratio, max_invalid_ratio,
        ))

    rating_ratio = rating_changes / max(incoming, 1)
    if rating_ratio > max_rating_change_ratio:
        anomalies.append(Anomaly(
            "RATING_CHANGE_SPIKE", "warning",
            f"Rating changes affect {rating_ratio:.1%} of incoming records.",
            "rating_change_ratio", rating_ratio, max_rating_change_ratio,
        ))

    if incoming_records > 0 and final_records == 0:
        anomalies.append(Anomaly(
            "EMPTY_FINAL_DATASET", "critical",
            "The refresh produced an empty final dataset.",
            "final_records", float(final_records), 1.0,
        ))

    return anomalies
