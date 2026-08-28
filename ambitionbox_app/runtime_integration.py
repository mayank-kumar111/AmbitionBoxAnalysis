"""Flask integration helpers for live dataset reloads."""

from __future__ import annotations

from flask import Flask

from .data_runtime import DatasetRuntime


def attach_dataset_runtime(
    app: Flask,
    *,
    runtime: DatasetRuntime,
    set_frame,
    rebuild_meta,
) -> DatasetRuntime:
    """Attach a DatasetRuntime to Flask's request lifecycle.

    On each request, reload the dataset if the source CSV fingerprint changed.
    The supplied setters update the app's in-memory frame/metadata references.
    """

    @app.before_request
    def _refresh_dataset_runtime() -> None:
        frame = runtime.get()
        set_frame(frame)
        rebuild_meta(frame)

    return runtime


__all__ = ["attach_dataset_runtime"]
