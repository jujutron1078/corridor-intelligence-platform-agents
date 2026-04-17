"""Shared utility functions used across all pipelines."""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger("corridor")


# ── Paths ─────────────────────────────────────────────────────────────────────

# src/shared/pipeline/utils.py → up 4 levels to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# CORRIDOR_DATA_ROOT overrides the default data/ location — used when data lives
# on a separately-mounted volume, an rclone-mounted R2/S3 bucket, or a shared NFS.
# For s3://-style URLs, services should use fsspec directly instead of Path.
_data_override = os.environ.get("CORRIDOR_DATA_ROOT")
DATA_DIR = Path(_data_override).expanduser() if _data_override else PROJECT_ROOT / "data"

_outputs_override = os.environ.get("CORRIDOR_OUTPUTS_ROOT")
OUTPUTS_DIR = Path(_outputs_override).expanduser() if _outputs_override else PROJECT_ROOT / "outputs"


def ensure_dir(path: Path) -> Path:
    """Create directory if it doesn't exist, return the path."""
    path.mkdir(parents=True, exist_ok=True)
    return path


# ── JSON/GeoJSON helpers ─────────────────────────────────────────────────────

def save_geojson(data: dict, path: Path) -> None:
    """Write a GeoJSON dict to file."""
    ensure_dir(path.parent)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    logger.info("Saved GeoJSON: %s (%d features)", path, len(data.get("features", [])))


def load_geojson(path: Path) -> dict:
    """Read a GeoJSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ── Rate limiting ────────────────────────────────────────────────────────────

class RateLimiter:
    """Simple token-bucket rate limiter."""

    def __init__(self, max_calls: int, period_seconds: float):
        self.max_calls = max_calls
        self.period = period_seconds
        self._calls: list[float] = []

    def wait(self) -> None:
        """Block until a call is allowed."""
        now = time.time()
        self._calls = [t for t in self._calls if now - t < self.period]
        if len(self._calls) >= self.max_calls:
            sleep_time = self.period - (now - self._calls[0])
            if sleep_time > 0:
                logger.debug("Rate limit: sleeping %.1fs", sleep_time)
                time.sleep(sleep_time)
        self._calls.append(time.time())


# ── Retry helper ─────────────────────────────────────────────────────────────

def retry(fn, max_retries: int = 3, backoff: float = 2.0, exceptions=(Exception,)):
    """Call *fn* with exponential backoff on failure."""
    for attempt in range(max_retries):
        try:
            return fn()
        except exceptions as exc:
            if attempt == max_retries - 1:
                raise
            wait = backoff ** attempt
            logger.warning("Retry %d/%d after %.1fs: %s", attempt + 1, max_retries, wait, exc)
            time.sleep(wait)


# ── Logging setup ────────────────────────────────────────────────────────────

def setup_logging(level: str = "INFO") -> None:
    """Configure console logging — JSON, Rich, or plain depending on env."""
    log_format = os.environ.get("LOG_FORMAT", "").lower()

    if log_format == "json":
        try:
            from pythonjsonlogger.json import JsonFormatter
            handler = logging.StreamHandler()
            handler.setFormatter(JsonFormatter(
                fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
                rename_fields={"asctime": "timestamp", "levelname": "level", "name": "logger"},
            ))
        except ImportError:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    else:
        try:
            from rich.logging import RichHandler
            handler = RichHandler(rich_tracebacks=True)
        except ImportError:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))

    logging.basicConfig(level=getattr(logging, level.upper()), handlers=[handler])


# ── Environment ──────────────────────────────────────────────────────────────

def load_env() -> None:
    """Load .env file from project root if it exists."""
    from dotenv import load_dotenv
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        load_dotenv(env_path)


def get_env(key: str, default: str | None = None, required: bool = False) -> str:
    """Get an environment variable with optional requirement check."""
    value = os.environ.get(key, default)
    if required and not value:
        raise EnvironmentError(f"Required environment variable {key} is not set")
    return value
