"""Token helpers for refresh and admin operations."""

from __future__ import annotations

import hashlib
import hmac
import os


def _candidate_hash(token: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}:{token}".encode("utf-8")).hexdigest()


def verify_configured_token(token: str, *, raw_env: str, hash_env: str, salt_env: str) -> bool:
    """Verify a supplied token against a raw token or salted SHA-256 hash."""
    supplied = (token or "").strip()
    if not supplied:
        return False

    expected_hash = os.getenv(hash_env, "").strip()
    salt = os.getenv(salt_env, "").strip()
    if expected_hash and salt:
        return hmac.compare_digest(_candidate_hash(supplied, salt), expected_hash)

    expected_raw = os.getenv(raw_env, "").strip()
    return bool(expected_raw) and hmac.compare_digest(supplied, expected_raw)


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
