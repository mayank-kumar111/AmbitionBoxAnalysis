import hashlib


def test_hashed_token_verification(monkeypatch):
    from ambitionbox_app.token_auth import admin_token_valid, refresh_token_valid

    salt = "unit-salt"
    refresh = "refresh-secret"
    admin = "admin-secret"
    monkeypatch.setenv("AMBITIONBOX_REFRESH_TOKEN_HASH", hashlib.sha256(f"{salt}:{refresh}".encode()).hexdigest())
    monkeypatch.setenv("AMBITIONBOX_REFRESH_TOKEN_SALT", salt)
    monkeypatch.setenv("AMBITIONBOX_ADMIN_TOKEN_HASH", hashlib.sha256(f"{salt}:{admin}".encode()).hexdigest())
    monkeypatch.setenv("AMBITIONBOX_ADMIN_TOKEN_SALT", salt)
    monkeypatch.delenv("AMBITIONBOX_REFRESH_TOKEN", raising=False)
    monkeypatch.delenv("AMBITIONBOX_ADMIN_TOKEN", raising=False)

    assert refresh_token_valid(refresh)
    assert not refresh_token_valid("wrong")
    assert admin_token_valid(admin)
    assert not admin_token_valid("wrong")


def test_raw_token_fallback(monkeypatch):
    from ambitionbox_app.token_auth import admin_token_valid, refresh_token_valid

    monkeypatch.setenv("AMBITIONBOX_REFRESH_TOKEN", "raw-refresh")
    monkeypatch.setenv("AMBITIONBOX_ADMIN_TOKEN", "raw-admin")
    for name in (
        "AMBITIONBOX_REFRESH_TOKEN_HASH",
        "AMBITIONBOX_REFRESH_TOKEN_SALT",
        "AMBITIONBOX_ADMIN_TOKEN_HASH",
        "AMBITIONBOX_ADMIN_TOKEN_SALT",
    ):
        monkeypatch.delenv(name, raising=False)

    assert refresh_token_valid("raw-refresh")
    assert admin_token_valid("raw-admin")
