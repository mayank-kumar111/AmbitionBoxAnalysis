from src.quality.monitor import summarize_health_runs


def test_summarize_health_runs():
    result = summarize_health_runs([
        {"snapshot_at": "2026-08-27", "health_score": 100, "health_status": "Healthy"},
        {"snapshot_at": "2026-08-28", "health_score": 80, "health_status": "Warning"},
        {"snapshot_at": "2026-08-29", "health_score": 40, "health_status": "Blocked"},
    ])

    assert result["latest"]["health_score"] == 40
    assert result["healthy_runs"] == 1
    assert result["warning_runs"] == 1
    assert result["blocked_runs"] == 1
    assert result["average_score"] == 73.3


def test_empty_health_runs():
    result = summarize_health_runs([])
    assert result["latest"] is None
    assert result["average_score"] is None
