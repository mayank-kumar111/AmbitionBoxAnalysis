"""Runtime dataset loader with change detection and atomic cache invalidation."""

from __future__ import annotations

import os
from pathlib import Path
from threading import RLock
from typing import Callable, Any

import pandas as pd

from .cache import TTLCache


class DatasetRuntime:
    """Lazily reload a CSV when its file fingerprint changes.

    The loader is thread-safe and only replaces the in-memory frame after a
    successful read, so a transient or partial write cannot discard the last
    known-good dataset.
    """

    def __init__(
        self,
        path: str | Path,
        loader: Callable[[Path], pd.DataFrame],
        cache: TTLCache | None = None,
    ) -> None:
        self.path = Path(path)
        self.loader = loader
        self.cache = cache
        self._lock = RLock()
        self._fingerprint: tuple[int, int] | None = None
        self._data: pd.DataFrame | None = None
        self._reloads = 0

    def fingerprint(self) -> tuple[int, int]:
        stat = os.stat(self.path)
        return stat.st_mtime_ns, stat.st_size

    def get(self) -> pd.DataFrame:
        current = self.fingerprint()
        if self._data is not None and self._fingerprint == current:
            return self._data

        with self._lock:
            current = self.fingerprint()
            if self._data is not None and self._fingerprint == current:
                return self._data

            fresh = self.loader(self.path)
            if not isinstance(fresh, pd.DataFrame):
                raise TypeError("dataset loader must return a pandas DataFrame")

            self._data = fresh
            self._fingerprint = current
            self._reloads += 1
            if self.cache is not None:
                self.cache.clear()
            return fresh

    @property
    def reload_count(self) -> int:
        return self._reloads

    @property
    def version(self) -> str:
        fp = self._fingerprint
        if fp is None:
            return "unloaded"
        return f"{fp[0]}:{fp[1]}"


__all__ = ["DatasetRuntime"]
