"""Small role-based access helpers for Data Operations endpoints."""

from __future__ import annotations

import os
from functools import wraps
from typing import Callable, Any

from flask import jsonify, request


def _admin_token() -> str:
    return os.getenv("AMBITIONBOX_ADMIN_TOKEN", "").strip()


def is_admin_request() -> bool:
    """Return True only when an operations/admin token is configured and matched."""
    token = _admin_token()
    if not token:
        return False
    supplied = request.headers.get("X-Admin-Token", "")
    return supplied == token


def require_admin(view: Callable[..., Any]) -> Callable[..., Any]:
    """Protect mutating operations endpoints with an admin token."""
    @wraps(view)
    def wrapped(*args: Any, **kwargs: Any):
        if not is_admin_request():
            return jsonify({"error": "Admin authorization required."}), 403
        return view(*args, **kwargs)
    return wrapped


__all__ = ["is_admin_request", "require_admin"]
