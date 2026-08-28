"""Environment-based configuration for the Flask application."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().casefold() in {"1", "true", "yes", "on"}


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc


class AppConfig:
    """Runtime settings loaded from environment variables."""

    DEBUG = _bool_env("FLASK_DEBUG", False)
    HOST = os.getenv("FLASK_HOST", "127.0.0.1")
    PORT = _int_env("FLASK_PORT", 5000)
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-only-change-me")
    DATABASE_PATH = os.getenv("AMBITIONBOX_DB_PATH", "data/ambitionbox.db")
    DATA_PATH = os.getenv("AMBITIONBOX_DATA_PATH", "")


class ProductionConfig(AppConfig):
    """Production-safe defaults; secrets should be supplied via environment."""

    DEBUG = False
    HOST = os.getenv("FLASK_HOST", "0.0.0.0")
    PORT = _int_env("FLASK_PORT", 8000)
