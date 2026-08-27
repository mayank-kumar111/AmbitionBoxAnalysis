from ambitionbox_app.data_quality_routes import _report_summary


def test_report_summary_counts_rating_changes_and_duplicates():
    report = {
        "snapshot": "20260827T193000Z",
        "previous_records": 100,
        "incoming_records": 12,
        "new_records": 8,
        "updated_records": 2,
        "unchanged_records": 2,
        "incoming_duplicate_rows": 1,
        "collapsed_records": 1,
        "invalid_records": 0,
        "applied": True,
        "updated_companies": [
            {"company_name": "A", "changes": {"company_rating": {"old": 4.0, "new": 4.2}}},
            {"company_name": "B", "changes": {"industry": {"old": "IT", "new": "Finance"}}},
        ],
    }

    summary = _report_summary(report)
    assert summary["available"] is True
    assert summary["new_records"] == 8
    assert summary["updated_records"] == 2
    assert summary["duplicate_records"] == 1
    assert summary["rating_changes"] == 1
    assert summary["applied"] is True


def test_empty_report_summary_is_safe():
    summary = _report_summary(None)
    assert summary["available"] is False
    assert summary["new_records"] == 0
    assert summary["duplicate_records"] == 0
