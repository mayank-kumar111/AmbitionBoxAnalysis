from src.quality.alerts import alert_summary, build_alerts


def test_build_alerts_from_warning_and_critical_anomalies():
    report = {
        "snapshot": "2026-08-28T00:00:00Z",
        "applied": False,
        "health": {"score": 40, "status": "Blocked"},
        "anomalies": [
            {
                "code": "DUPLICATE_SPIKE",
                "severity": "warning",
                "message": "Duplicate rate is high.",
                "metric": "duplicate_ratio",
                "value": 0.2,
                "threshold": 0.05,
            },
            {
                "code": "EMPTY_FINAL_DATASET",
                "severity": "critical",
                "message": "Final dataset is empty.",
                "metric": "final_records",
                "value": 0,
                "threshold": 1,
            },
        ],
    }

    alerts = build_alerts(report)
    assert len(alerts) == 2
    assert alerts[0]["code"] == "DUPLICATE_SPIKE"
    assert alerts[1]["severity"] == "critical"


def test_alert_summary_is_empty_for_healthy_run():
    result = alert_summary({
        "health": {"score": 100, "status": "Healthy"},
        "anomalies": [],
        "applied": True,
    })
    assert result["alert_count"] == 0
    assert result["critical_count"] == 0
    assert result["status"] == "Healthy"
