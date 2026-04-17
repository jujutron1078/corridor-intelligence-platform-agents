"""
ACLED service — serves cached conflict event data.
"""

from __future__ import annotations

import logging
from typing import Any

from src.pipelines.acled_pipeline.fetcher import load_events

logger = logging.getLogger("corridor.api.acled_service")

_data: dict = {}
_loaded = False


def init() -> None:
    """Load cached ACLED conflict data."""
    global _data, _loaded
    _data = load_events()
    count = len(_data.get("features", []))
    if count > 0:
        logger.info("ACLED service loaded: %d conflict events", count)
    else:
        logger.warning("No ACLED data cached. Set ACLED_USERNAME and ACLED_PASSWORD in .env and run 'python run_all.py pull'.")
    _loaded = True


def is_loaded() -> bool:
    """Check if data is loaded."""
    return _loaded and bool(_data.get("features"))


def get_conflict_events(
    country: str | None = None,
    year: int | None = None,
    event_type: str | None = None,
) -> dict[str, Any]:
    """
    Get conflict events, optionally filtered.

    Args:
        country: Filter by country name (e.g., "Nigeria")
        year: Filter by year
        event_type: Filter by event type (Battles, Protests, etc.)

    Returns GeoJSON FeatureCollection with summary stats.
    """
    features = _data.get("features", [])

    if country:
        features = [
            f for f in features
            if f["properties"].get("country", "").lower() == country.lower()
        ]
    if year:
        features = [
            f for f in features
            if f["properties"].get("year") == year
        ]
    if event_type:
        features = [
            f for f in features
            if f["properties"].get("event_type", "").lower() == event_type.lower()
        ]

    # Compute summary stats
    total_fatalities = sum(f["properties"].get("fatalities", 0) for f in features)

    # Event type breakdown
    type_counts: dict[str, int] = {}
    for f in features:
        et = f["properties"].get("event_type", "Unknown")
        type_counts[et] = type_counts.get(et, 0) + 1

    # Country breakdown
    country_counts: dict[str, int] = {}
    for f in features:
        c = f["properties"].get("country", "Unknown")
        country_counts[c] = country_counts.get(c, 0) + 1

    return {
        "type": "FeatureCollection",
        "features": features,
        "summary": {
            "total_events": len(features),
            "total_fatalities": total_fatalities,
            "by_event_type": type_counts,
            "by_country": country_counts,
        },
    }
