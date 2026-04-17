"""
Agriculture enriched service — serves crop production, export, and yield data.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from src.shared.pipeline.utils import DATA_DIR

logger = logging.getLogger("corridor.api.agriculture_enriched_service")

AGRICULTURE_DATA_DIR = DATA_DIR / "agriculture_enriched"

_data: list = []
_loaded = False


def init() -> None:
    """Load cached agriculture enriched data."""
    global _data, _loaded

    path = AGRICULTURE_DATA_DIR / "agriculture.json"
    if path.exists():
        _data = json.load(open(path, encoding="utf-8"))
        logger.info("Agriculture enriched service loaded: %d records", len(_data))
    else:
        logger.warning(
            "No agriculture data. Run the agriculture_enriched pipeline to generate agriculture.json."
        )
        _data = []

    _loaded = True


def is_loaded() -> bool:
    return _loaded and bool(_data)


def get_crops(
    country: str | None = None,
    crop: str | None = None,
) -> list[dict[str, Any]]:
    """
    Get crop records, optionally filtered by country name and/or crop name.

    country — matches the 'country' field (e.g. 'Ghana', 'Nigeria').
    crop    — case-insensitive substring match against the 'crop' field.
    """
    records = _data

    if country:
        records = [
            r for r in records
            if country.lower() in r.get("country", "").lower()
        ]
    if crop:
        records = [
            r for r in records
            if crop.lower() in r.get("crop", "").lower()
        ]

    return records


def get_summary() -> dict[str, Any]:
    """
    Return summary statistics: total records, distinct countries and crops,
    plus per-country record counts.
    """
    countries: set[str] = set()
    crops: set[str] = set()
    by_country: dict[str, int] = {}

    for r in _data:
        c = r.get("country", "UNKNOWN")
        cr = r.get("crop", "UNKNOWN")
        countries.add(c)
        crops.add(cr)
        by_country[c] = by_country.get(c, 0) + 1

    return {
        "total_records": len(_data),
        "countries": sorted(countries),
        "crops": sorted(crops),
        "by_country": by_country,
    }
