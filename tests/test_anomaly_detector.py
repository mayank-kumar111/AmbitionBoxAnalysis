from src.quality.anomaly_detector import detect_anomalies


def test_large_growth_is_flagged():
    anomalies = detect_anomalies(
        previous_records=100,
        incoming_records=140,
        final_records=140,
        new_records=40,
        updated_records=0,
        duplicate_records=0,
        invalid_records=0,
    )
    assert any(item.code == "LARGE_DATASET_GROWTH" for item in anomalies)


def test_duplicate_and_invalid_spikes_are_flagged():
    anomalies = detect_anomalies(
        previous_records=100,
        incoming_records=100,
        final_records=100,
        new_records=0,
        updated_records=0,
        duplicate_records=10,
        invalid_records=3,
    )
    codes = {item.code for item in anomalies}
    assert "DUPLICATE_SPIKE" in codes
    assert "INVALID_RECORD_SPIKE" in codes


def test_critical_drop_is_flagged():
    anomalies = detect_anomalies(
        previous_records=100,
        incoming_records=50,
        final_records=80,
        new_records=0,
        updated_records=0,
        duplicate_records=0,
        invalid_records=0,
        removed_records=30,
    )
    assert any(item.code == "LARGE_DATASET_DROP" and item.severity == "critical" for item in anomalies)


def test_clean_refresh_has_no_anomalies():
    anomalies = detect_anomalies(
        previous_records=1000,
        incoming_records=100,
        final_records=1050,
        new_records=50,
        updated_records=10,
        duplicate_records=1,
        invalid_records=0,
        rating_changes=2,
    )
    assert anomalies == []
