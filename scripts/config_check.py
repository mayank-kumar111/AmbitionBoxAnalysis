"""Validate AmbitionBox Analysis runtime configuration before startup/deployment."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv


def _bool_value(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    if value.strip().casefold() in {"1", "true", "yes", "on"}:
        return True
    if value.strip().casefold() in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be true/false")


def _int_value(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc


def validate_environment(*, production: bool = False) -> dict[str, object]:
    """Validate configuration without printing or exposing secret values."""
    load_dotenv()
    errors: list[str] = []
    warnings: list[str] = []

    try:
        debug = _bool_value("FLASK_DEBUG", False)
    except ValueError as exc:
        errors.append(str(exc))
        debug = False

    try:
        port = _int_value("FLASK_PORT", 8000 if production else 5000)
        if not 1 <= port <= 65535:
            errors.append("FLASK_PORT must be between 1 and 65535")
    except ValueError as exc:
        errors.append(str(exc))
        port = 8000 if production else 5000

    secret = os.getenv("FLASK_SECRET_KEY", os.getenv("SECRET_KEY", ""))
    if production:
        if not secret or secret in {"change-this-in-production", "dev-only-change-me"}:
            errors.append("A non-default FLASK_SECRET_KEY is required in production")
        if debug:
            errors.append("FLASK_DEBUG must be false in production")
    elif debug and not secret:
        warnings.append("FLASK_DEBUG is enabled without an explicit secret key")

    data_path = Path(os.getenv("AMBITIONBOX_DATA_PATH", "ambitionbox_app/data/companies.csv"))
    db_path = Path(os.getenv("AMBITIONBOX_DB_PATH", "data/ambitionbox.db"))
    if not data_path.exists():
        warnings.append(f"Dataset file not found: {data_path}")
    if not db_path.parent.exists():
        warnings.append(f"Database parent directory will be created: {db_path.parent}")

    host = os.getenv("FLASK_HOST", "0.0.0.0" if production else "127.0.0.1")
    return {
        "valid": not errors,
        "production": production,
        "host": host,
        "port": port,
        "debug": debug,
        "data_path": str(data_path),
        "database_path": str(db_path),
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate AmbitionBox runtime configuration")
    parser.add_argument("--production", action="store_true", help="Apply production safety checks")
    args = parser.parse_args()

    result = validate_environment(production=args.production)
    print(f"Configuration: {'VALID' if result['valid'] else 'INVALID'}")
    print(f"Mode: {'production' if args.production else 'development'}")
    print(f"Host: {result['host']}")
    print(f"Port: {result['port']}")
    print(f"Debug: {result['debug']}")
    print(f"Data path: {result['data_path']}")
    print(f"Database path: {result['database_path']}")
    for warning in result["warnings"]:
        print(f"WARNING: {warning}")
    for error in result["errors"]:
        print(f"ERROR: {error}")
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
