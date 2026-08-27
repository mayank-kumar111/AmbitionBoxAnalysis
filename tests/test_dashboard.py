"""Smoke tests for the Flask dashboard APIs."""

from __future__ import annotations

from ambitionbox_app.app import app


def test_meta_api_returns_dataset_health_metrics():
    client = app.test_client()
    response = client.get("/api/meta")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload is not None
    assert payload["totals"]["companies"] > 0
    assert payload["totals"]["industries"] >= 0
    assert payload["totals"]["locations"] >= 0


def test_dashboard_page_loads():
    client = app.test_client()
    response = client.get("/dashboard")

    assert response.status_code == 200
    assert b"Dataset health" in response.data
