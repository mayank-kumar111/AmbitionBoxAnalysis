import os


def test_apply_requires_admin_token(monkeypatch):
    from flask import Flask
    from ambitionbox_app import refresh_routes

    app = Flask(__name__)
    refresh_routes.register_refresh_routes(app)
    monkeypatch.setenv("AMBITIONBOX_REFRESH_TOKEN", "refresh-secret")
    monkeypatch.setenv("AMBITIONBOX_ADMIN_TOKEN", "admin-secret")

    client = app.test_client()
    response = client.post(
        "/api/refresh",
        json={"pages": 1, "apply": True},
        headers={"X-Refresh-Token": "refresh-secret"},
    )
    assert response.status_code == 403


def test_apply_accepts_admin_token_on_loopback(monkeypatch):
    from flask import Flask
    from ambitionbox_app import refresh_routes

    class DummyProcess:
        pid = 123

        def poll(self):
            return 0

    app = Flask(__name__)
    refresh_routes.register_refresh_routes(app)
    monkeypatch.setenv("AMBITIONBOX_REFRESH_TOKEN", "refresh-secret")
    monkeypatch.setenv("AMBITIONBOX_ADMIN_TOKEN", "admin-secret")
    monkeypatch.setattr(refresh_routes.subprocess, "Popen", lambda *a, **k: DummyProcess())

    client = app.test_client()
    response = client.post(
        "/api/refresh",
        json={"pages": 1, "apply": True},
        headers={
            "X-Refresh-Token": "refresh-secret",
            "X-Admin-Token": "admin-secret",
        },
    )
    assert response.status_code == 202


def test_dry_run_does_not_require_admin_token(monkeypatch):
    from flask import Flask
    from ambitionbox_app import refresh_routes

    class DummyProcess:
        pid = 456

    app = Flask(__name__)
    refresh_routes.register_refresh_routes(app)
    monkeypatch.setenv("AMBITIONBOX_REFRESH_TOKEN", "refresh-secret")
    monkeypatch.setenv("AMBITIONBOX_ADMIN_TOKEN", "admin-secret")
    monkeypatch.setattr(refresh_routes.subprocess, "Popen", lambda *a, **k: DummyProcess())

    client = app.test_client()
    response = client.post(
        "/api/refresh",
        json={"pages": 1, "apply": False},
        headers={"X-Refresh-Token": "refresh-secret"},
    )
    assert response.status_code == 202
