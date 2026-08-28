from ambitionbox_app.config import _bool_env, _int_env


def test_bool_env(monkeypatch):
    monkeypatch.setenv("TEST_BOOL", "YeS")
    assert _bool_env("TEST_BOOL", False) is True


def test_int_env(monkeypatch):
    monkeypatch.setenv("TEST_INT", "8123")
    assert _int_env("TEST_INT", 5000) == 8123
