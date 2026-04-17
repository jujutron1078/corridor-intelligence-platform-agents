"""
In-memory TTL cache for GEE results and API responses.

Key format: "nightlights:2023:6" → {tile_url, stats, timestamp}
TTL: 1 hour for time-series data, 24 hours for static layers.
Max size: ~500 entries.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from src.api.config import CACHE_TTL_SECONDS, CACHE_TTL_STATIC, CACHE_MAX_SIZE

logger = logging.getLogger("corridor.api.cache")


class TTLCache:
    """Simple in-memory TTL cache with size limit."""

    def __init__(self, default_ttl: int = CACHE_TTL_SECONDS, max_size: int = CACHE_MAX_SIZE):
        self._store: dict[str, dict[str, Any]] = {}
        self._default_ttl = default_ttl
        self._max_size = max_size
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Any | None:
        """Get a value from the cache. Returns None if missing or expired."""
        entry = self._store.get(key)
        if entry is None:
            self._misses += 1
            return None

        if time.time() > entry["expires_at"]:
            del self._store[key]
            self._misses += 1
            return None

        self._hits += 1
        return entry["value"]

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Store a value with TTL."""
        if len(self._store) >= self._max_size:
            self._evict()

        self._store[key] = {
            "value": value,
            "expires_at": time.time() + (ttl or self._default_ttl),
            "created_at": time.time(),
        }

    def _evict(self) -> None:
        """Remove expired entries and oldest entries if still over limit."""
        now = time.time()

        # Remove expired first
        expired_keys = [k for k, v in self._store.items() if now > v["expires_at"]]
        for k in expired_keys:
            del self._store[k]

        # If still over limit, remove oldest
        if len(self._store) >= self._max_size:
            sorted_keys = sorted(self._store.keys(), key=lambda k: self._store[k]["created_at"])
            remove_count = len(self._store) - self._max_size + 50  # clear some headroom
            for k in sorted_keys[:remove_count]:
                del self._store[k]

    def clear(self) -> None:
        """Clear all cache entries."""
        self._store.clear()
        self._hits = 0
        self._misses = 0

    @property
    def stats(self) -> dict[str, int]:
        """Return cache hit/miss statistics."""
        return {
            "size": len(self._store),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / max(1, self._hits + self._misses), 3),
        }


def make_cache_key(*parts: Any) -> str:
    """Build a cache key from parts."""
    return ":".join(str(p) for p in parts)


# ── Singleton cache instances ────────────────────────────────────────────────

# For GEE tile URLs and stats (1h TTL for temporal, 24h for static)
gee_cache = TTLCache(default_ttl=CACHE_TTL_SECONDS)

# For processed data (GeoJSON, trade data)
data_cache = TTLCache(default_ttl=CACHE_TTL_STATIC)
