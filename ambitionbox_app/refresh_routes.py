"""Safe local refresh controls for the AmbitionBox Flask app."""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from flask import jsonify, request


ROOT_DIR = Path(__file__).resolve().parent.parent
REFRESH_SCRIPT = ROOT_DIR / "scripts" / "refresh_pipeline.py"
MAX_PAGES = 10

_state_lock = threading.RLock()
_active_process: subprocess.Popen[str] | None = None
_active_job: dict[str, Any] | None = None


def _authorized() -> bool:
    """Allow loopback by default; require a token for non-loopback use."""
    remote = request.remote_addr or ""
    token = os.getenv("AMBITIONBOX_REFRESH_TOKEN", "").strip()
    if token:
        supplied = request.headers.get("X-Refresh-Token", "")
        return supplied == token
    return remote in {"127.0.0.1", "::1", "localhost"}


def _cleanup_finished() -> None:
    global _active_process, _active_job
    with _state_lock:
        if _active_process is not None and _active_process.poll() is not None:
            code = _active_process.returncode
            if _active_job is not None:
                _active_job["status"] = "completed" if code == 0 else "failed"
                _active_job["return_code"] = code
                _active_job["finished_at"] = time.time()
            _active_process = None


def register_refresh_routes(app) -> None:
    @app.route("/api/refresh", methods=["POST"])
    def api_refresh():
        if not _authorized():
            return jsonify({"error": "Refresh endpoint is not authorized."}), 403

        payload = request.get_json(silent=True) or {}
        try:
            pages = int(payload.get("pages", 1))
        except (TypeError, ValueError):
            return jsonify({"error": "pages must be an integer"}), 400
        if pages < 1 or pages > MAX_PAGES:
            return jsonify({"error": f"pages must be between 1 and {MAX_PAGES}"}), 400

        extended = bool(payload.get("extended", False))
        apply = bool(payload.get("apply", False))
        full_snapshot = bool(payload.get("full_snapshot", False))

        _cleanup_finished()
        global _active_process, _active_job
        with _state_lock:
            if _active_process is not None and _active_process.poll() is None:
                return jsonify({
                    "error": "A refresh is already running.",
                    "job": _active_job,
                }), 409

            command = [
                sys.executable,
                str(REFRESH_SCRIPT),
                "--pages", str(pages),
            ]
            if extended:
                command.append("--extended")
            if apply:
                command.append("--apply")
            if full_snapshot:
                command.append("--full-snapshot")

            process = subprocess.Popen(
                command,
                cwd=ROOT_DIR,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            _active_process = process
            _active_job = {
                "job_id": uuid.uuid4().hex,
                "status": "running",
                "pages": pages,
                "extended": extended,
                "apply": apply,
                "full_snapshot": full_snapshot,
                "pid": process.pid,
                "started_at": time.time(),
            }
            return jsonify({"message": "Refresh started.", "job": _active_job}), 202

    @app.route("/api/refresh/status", methods=["GET"])
    def api_refresh_status():
        if not _authorized():
            return jsonify({"error": "Refresh endpoint is not authorized."}), 403
        _cleanup_finished()
        with _state_lock:
            return jsonify({"job": _active_job})
