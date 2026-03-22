"""Generic TTL cache for network data (yields, hacks, token maps, etc.)."""

from __future__ import annotations

import time
from typing import Any


class TTLCache:
    """Simple in-memory cache with time-to-live expiration."""

    def __init__(self, ttl_seconds: float = 600.0):
        self.ttl = ttl_seconds
        self._data: Any = None
        self._timestamp: float = 0.0

    @property
    def is_valid(self) -> bool:
        return self._data is not None and (time.time() - self._timestamp) < self.ttl

    def get(self) -> Any:
        if self.is_valid:
            return self._data
        return None

    def set(self, data: Any) -> None:
        self._data = data
        self._timestamp = time.time()

    @property
    def age(self) -> float:
        return time.time() - self._timestamp
