"""Small bounded TTL cache for expensive Flask computations."""

from __future__ import annotations

import time
from collections import OrderedDict
from threading import RLock
from typing import Any, Callable


class TTLCache:
    """Thread-safe LRU cache with a time-to-live."""

    def __init__(self, maxsize: int = 128, ttl_seconds: float = 30.0) -> None:
        if maxsize < 1:
            raise ValueError("maxsize must be at least 1")
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        self.maxsize = maxsize
        self.ttl_seconds = ttl_seconds
        self._items: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self._lock = RLock()

    def get(self, key: str) -> Any | None:
        now = time.monotonic()
        with self._lock:
            item = self._items.get(key)
            if item is None:
                return None
            created, value = item
            if now - created >= self.ttl_seconds:
                self._items.pop(key, None)
                return None
            self._items.move_to_end(key)
            return value

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._items[key] = (time.monotonic(), value)
            self._items.move_to_end(key)
            while len(self._items) > self.maxsize:
                self._items.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()

    def stats(self) -> dict[str, int]:
        with self._lock:
            return {"size": len(self._items), "maxsize": self.maxsize}


def make_cache_key(prefix: str, query_string: str) -> str:
    return f"{prefix}:{query_string}"


__all__ = ["TTLCache", "make_cache_key"]
