"""Persistent audit trail for refresh operations."""

from __future__ import annotations

import json
import os
import socket
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
AUDIT_PATH = ROOT_DIR / "data" / "refresh_audit.jsonl"
_LOCK = threading.RLock()


def record_event(
    *,
    action: str,
    actor: str = "local-user",
    status: str = "started",
    job_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    event = {
        "event_id": uuid.uuid4().hex,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "actor": actor,
        "status": status,
        "job_id": job_id,
        "host": socket.gethostname(),
        "details": details or {},
    }
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        with AUDIT_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, default=str) + "\n")
    return event


def list_events(limit: int = 50) -> list[dict[str, Any]]:
    limit = max(1, min(200, int(limit)))
    if not AUDIT_PATH.exists():
        return []
    with _LOCK:
        lines = AUDIT_PATH.read_text(encoding="utf-8").splitlines()
    events: list[dict[str, Any]] = []
    for line in reversed(lines[-limit:]):
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            events.append(payload)
    return events


__all__ = ["record_event", "list_events", "AUDIT_PATH"]
