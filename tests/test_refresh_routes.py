from ambitionbox_app.app import app
import ambitionbox_app.refresh_routes as refresh_routes


class FakeProcess:
    def __init__(self, return_code=None):
        self.pid = 12345
        self.returncode = return_code
        self._running = return_code is None

    def poll(self):
        return None if self._running else self.returncode


def reset_state():
    refresh_routes._active_process = None
    refresh_routes._active_job = None


def test_refresh_requires_valid_pages(monkeypatch):
    reset_state()
    client = app.test_client()
    response = client.post("/api/refresh", json={"pages": 0})
    assert response.status_code == 400
    assert "pages must be between" in response.get_json()["error"]


def test_refresh_starts_dry_run(monkeypatch):
    reset_state()
    calls = []
    fake = FakeProcess()

    def fake_popen(command, **kwargs):
        calls.append(command)
        return fake

    monkeypatch.setattr(refresh_routes.subprocess, "Popen", fake_popen)
    client = app.test_client()
    response = client.post("/api/refresh", json={"pages": 2})

    assert response.status_code == 202
    assert calls
    command = calls[0]
    assert command[-2:] == ["--pages", "2"]
    assert "--apply" not in command
    assert response.get_json()["job"]["apply"] is False

    reset_state()


def test_refresh_starts_extended_apply(monkeypatch):
    reset_state()
    calls = []
    fake = FakeProcess()

    def fake_popen(command, **kwargs):
        calls.append(command)
        return fake

    monkeypatch.setattr(refresh_routes.subprocess, "Popen", fake_popen)
    client = app.test_client()
    response = client.post(
        "/api/refresh",
        json={"pages": 3, "extended": True, "apply": True},
    )

    assert response.status_code == 202
    command = calls[0]
    assert "--extended" in command
    assert "--apply" in command
    assert response.get_json()["job"]["extended"] is True
    assert response.get_json()["job"]["apply"] is True

    reset_state()


def test_refresh_rejects_second_active_run(monkeypatch):
    reset_state()
    refresh_routes._active_process = FakeProcess()
    refresh_routes._active_job = {"status": "running"}

    client = app.test_client()
    response = client.post("/api/refresh", json={"pages": 1})
    assert response.status_code == 409
    assert response.get_json()["error"] == "A refresh is already running."

    reset_state()
