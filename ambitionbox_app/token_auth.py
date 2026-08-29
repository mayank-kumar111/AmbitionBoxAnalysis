"""Token helpers for refresh and admin operations."""

from __future__ import annotations

import hashlib
import hmac
import os
import time


def _candidate_hash(token: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}:{token}".encode("utf-8")).hexdigest()


def _not_expired(env_name: str) -> bool:
    """Return True when an optional Unix-timestamp expiry is still valid."""
    raw = os.getenv(env_name, "").strip()
    if not raw:
        return True
    try:
        return time.time() < float(raw)
    except ValueError:
        return False


def _verify_pair(token: str, *, raw_env: str, hash_env: str, salt_env: str, expiry_env: str) -> bool:
    if not _not_expired(expiry_env):
        return False

    expected_hash = os.getenv(hash_env, "").strip()
    salt = os.getenv(salt_env, "").strip()
    if expected_hash and salt:
        return hmac.compare_digest(_candidate_hash(token, salt), expected_hash)

    expected_raw = os.getenv(raw_env, "").strip()
    return bool(expected_raw) and hmac.compare_digest(token, expected_raw)


def verify_configured_token(token: str, *, raw_env: str, hash_env: str, salt_env: str) -> bool:
    """Verify a supplied token against the active credential."""
    supplied = (token or "").strip()
    if not supplied:
        return False

    if _verify_pair(
        supplied,
        raw_env=raw_env,
        hash_env=hash_env,
        salt_env=salt_env,
        expiry_env=f"{raw_env}_EXPIRES_AT",
    ):
        return True

    previous_prefix = raw_env
    return _verify_pair(
        supplied,
        raw_env=f"{previous_prefix}_PREVIOUS",
        hash_env=f"{hash_env}_PREVIOUS",
        salt_env=f"{salt_env}_PREVIOUS",
        expiry_env=f"{previous_prefix}_PREVIOUS_EXPIRES_AT",
    )


def refresh_token_valid(token: str) -> bool:
    return verify_configured_token(
        token,
        raw_env="AMBITIONBOX_REFRESH_TOKEN",
        hash_env="AMBITIONBOX_REFRESH_TOKEN_HASH",
        salt_env="AMBITIONBOX_REFRESH_TOKEN_SALT",
    )


def admin_token_valid(token: str) -> bool:
    return verify_configured_token(
        token,
        raw_env="AMBITIONBOX_ADMIN_TOKEN",
        hash_env="AMBITIONBOX_ADMIN_TOKEN_HASH",
        salt_env="AMBITIONBOX_ADMIN_TOKEN_SALT",
    )


def configured_auth_mode(*, raw_env: str, hash_env: str, salt_env: str) -> str:
    if os.getenv(hash_env, "").strip() and os.getenv(salt_env, "").strip():
        return "hashed"
    if os.getenv(raw_env, "").strip():
        return "raw"
    return "loopback-only"


__all__ = ["admin_token_valid", "configured_auth_mode", "refresh_token_valid", "verify_configured_token"]
