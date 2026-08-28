from scripts.notify_refresh import build_message


def test_build_message_healthy_is_quiet():
    assert build_message({"health": {"status": "Healthy", "score": 100}}) is None


def test_build_message_warning_contains_metrics_and_anomaly():
    message = build_message({
        "health": {"status": "Warning", "score": 80},
        "snapshot": "2026-08-28T00:00:00Z",
        "new_records": 12,
        "updated_records": 5,
        "duplicate_records": 3,
        "rating_changes": 2,
        "applied": False,
        "anomalies": [{
            "severity": "warning",
            "code": "DUPLICATE_SPIKE",
            "message": "Duplicate rate is high.",
        }],
    })
    assert "Warning" in message
    assert "DUPLICATE_SPIKE" in message
    assert "New: 12" in message
    assert "not applied" in message


def test_build_message_blocked_contains_critical_anomaly():
    message = build_message({
        "health": {"status": "Blocked", "score": 40},
        "snapshot": "2026-08-28T00:00:00Z",
        "anomalies": [{
            "severity": "critical",
            "code": "LARGE_DATASET_DROP",
            "message": "Dataset dropped by 80%.",
        }],
        "applied": False,
    })
    assert "Blocked" in message
    assert "CRITICAL" in message
    assert "LARGE_DATASET_DROP" in message
