from ambitionbox_app.app import app


def test_health_endpoint():
    client = app.test_client()
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "ok"
    assert payload["service"] == "ambitionbox-analysis"
    assert payload["data_records"] > 0
