"""
Manufacturing service — serves industrial company and sector data.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from src.shared.pipeline.utils import DATA_DIR

logger = logging.getLogger("corridor.api.manufacturing_service")

MANUFACTURING_DATA_DIR = DATA_DIR / "manufacturing"

_data: list = []
_loaded = False


def init() -> None:
    """Load cached manufacturing data."""
    global _data, _loaded

    path = MANUFACTURING_DATA_DIR / "companies.json"
    if path.exists():
        _data = json.load(open(path, encoding="utf-8"))
        logger.info("Manufacturing service loaded: %d companies", len(_data))
    else:
        logger.warning(
            "No manufacturing data. Run the manufacturing pipeline to generate companies.json."
        )
        _data = []

    _loaded = True


def is_loaded() -> bool:
    return _loaded and bool(_data)


def get_companies(
    country: str | None = None,
    sector: str | None = None,
) -> list[dict[str, Any]]:
    """
    Get manufacturing companies, optionally filtered by country code or sector.
    """
    records = _data

    if country:
        records = [
            r for r in records
            if r.get("country_code", "").upper() == country.upper()
        ]
    if sector:
        records = [
            r for r in records
            if sector.lower() in r.get("sector", "").lower()
        ]

    return records


def get_summary() -> dict[str, Any]:
    """
    Return summary statistics: total count, breakdown by country and sector.
    """
    by_country: dict[str, int] = {}
    by_sector: dict[str, int] = {}

    for r in _data:
        cc = r.get("country_code", "UNKNOWN")
        by_country[cc] = by_country.get(cc, 0) + 1

        sec = r.get("sector", "UNKNOWN")
        by_sector[sec] = by_sector.get(sec, 0) + 1

    return {
        "total": len(_data),
        "by_country": by_country,
        "by_sector": by_sector,
    }
