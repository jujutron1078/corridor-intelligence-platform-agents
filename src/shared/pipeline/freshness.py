"""Data freshness tracking for pipeline outputs.

Records when each pipeline was last pulled and how many records were
saved. Provides staleness checks so the server can warn on startup
and the health endpoint can report data age.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.shared.pipeline.utils import DATA_DIR

logger = logging.getLogger("corridor.freshness")

FRESHNESS_PATH = DATA_DIR / "freshness.json"

# Maximum acceptable age (in days) before data is considered stale.
STALENESS_THRESHOLDS: dict[str, int] = {
    "osm": 30,           # streets / buildings change slowly
    "mineral": 180,      # USGS updates ~biannually
    "worldbank": 90,     # annual indicators, but check quarterly
    "energy": 180,       # power-plant DB updates ~biannually
    "acled": 7,          # conflict events update weekly
    "trade_prices": 30,  # World Bank Pink Sheet — monthly
    "trade_comtrade": 90,  # UN Comtrade — quarterly
    "health": 90,        # healthsites.io — check quarterly
    "imf": 90,            # IMF WEO — quarterly check
    "cpi": 365,           # Transparency International CPI — annual
    "vdem": 365,          # V-Dem governance — annual
    "gdl": 180,           # Global Data Lab HDI — biannual
    "aiddata": 180,       # AidData projects — biannual
    "gem": 90,            # Global Energy Monitor — quarterly
    "fao": 90,            # FAO FAOSTAT — quarterly
    "unctad": 180,        # UNCTAD port stats — biannual
    "energydata": 180,    # energydata.info grid — biannual
    "ppi": 180,           # IFC PPI database — biannual
    "gadm": 365,          # GADM admin boundaries — annual
    "wapp": 365,          # WAPP master plan — annual
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_freshness() -> dict[str, Any]:
    """Load freshness metadata from disk (empty dict if missing)."""
    if FRESHNESS_PATH.exists():
        try:
            with open(FRESHNESS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Could not read freshness file: %s", exc)
    return {}


def _save(data: dict[str, Any]) -> None:
    FRESHNESS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(FRESHNESS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def record_pull(pipeline: str, record_count: int = 0) -> None:
    """Record that *pipeline* was just pulled with *record_count* records."""
    data = load_freshness()
    data[pipeline] = {
        "pulled_at": _now_iso(),
        "records": record_count,
    }
    _save(data)
    logger.info("Freshness recorded: %s - %d records", pipeline, record_count)


def age_days(pipeline: str) -> float | None:
    """Return age of *pipeline* data in days, or None if never pulled."""
    entry = load_freshness().get(pipeline)
    if not entry or not entry.get("pulled_at"):
        return None
    pulled = datetime.fromisoformat(entry["pulled_at"])
    return (datetime.now(timezone.utc) - pulled).total_seconds() / 86400


def is_stale(pipeline: str) -> bool:
    """Return True if *pipeline* data is older than its threshold (or missing)."""
    days = age_days(pipeline)
    if days is None:
        return True
    threshold = STALENESS_THRESHOLDS.get(pipeline, 90)
    return days > threshold


def get_stale_pipelines() -> list[str]:
    """Return list of pipeline names that are stale or never pulled."""
    return [name for name in STALENESS_THRESHOLDS if is_stale(name)]


def get_freshness_report() -> dict[str, Any]:
    """Return a report suitable for the /api/health endpoint."""
    data = load_freshness()
    report: dict[str, Any] = {}
    for name, threshold in STALENESS_THRESHOLDS.items():
        entry = data.get(name, {})
        days = age_days(name)
        report[name] = {
            "pulled_at": entry.get("pulled_at"),
            "records": entry.get("records", 0),
            "age_days": round(days, 1) if days is not None else None,
            "max_age_days": threshold,
            "stale": is_stale(name),
        }
    return report
