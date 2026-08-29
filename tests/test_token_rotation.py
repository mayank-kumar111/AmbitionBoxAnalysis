import hashlib
import time


def _sha(salt, token):
    return hashlib.sha256(f"{salt}:{token}".encode()).hexdigest()


def test_previous_hashed_token_works_until_expiry(monkeypatch):
    from ambitionbox_app.token_auth import refresh_token_valid

    monkeypatch.setenv("AMBITIONBOX_REFRESH_TOKEN_HASH", _sha("new-salt", "new-token"))
    monkeypatch.setenv("AMBITIONBOX_REFRESH_TOKEN_SALT", "new-salt")
    monkeypatch.setenv("AMBITIONBOX_REFRESH_TOKEN_PREVIOUS_HASH", _sha("old-salt", "old-token"))
    monkeypatch.setenv("AMBITIONBOX_REFRESH_TOKEN_SALT_PREVIOUS", "old-salt")
    monkeypatch.setenv("AMBITIONBOX_REFRESH_TOKEN_PREVIOUS_EXPIRES_AT", str(time.time() + 60))

    assert refresh_token_valid("new-token")
    assert refresh_token_valid("old-token")


def test_previous_hashed_token_expires(monkeypatch):
    from ambitionbox_app.token_auth import refresh_token_valid

    monkeypatch.setenv("AMBITIONBOX_REFRESH_TOKEN_HASH", _sha("new-salt", "new-token"))
    monkeypatch.setenv("AMBITIONBOX_REFRESH_TOKEN_SALT", "new-salt")
    monkeypatch.setenv("AMBITIONBOX_REFRESH_TOKEN_PREVIOUS_HASH", _sha("old-salt", "old-token"))
    monkeypatch.setenv("AMBITIONBOX_REFRESH_TOKEN_SALT_PREVIOUS", "old-salt")
    monkeypatch.setenv("AMBITIONBOX_REFRESH_TOKEN_PREVIOUS_EXPIRES_AT", str(time.time() - 1))

    assert refresh_token_valid("new-token")
    assert not refresh_token_valid("old-token")


def test_current_token_expiry_rejects_token(monkeypatch):
    from ambitionbox_app.token_auth import admin_token_valid

    monkeypatch.setenv("AMBITIONBOX_ADMIN_TOKEN_HASH", _sha("salt", "admin-token"))
    monkeypatch.setenv("AMBITIONBOX_ADMIN_TOKEN_SALT", "salt")
    monkeypatch.setenv("AMBITIONBOX_ADMIN_TOKEN_EXPIRES_AT", str(time.time() - 1))

    assert not admin_token_valid("admin-token")
