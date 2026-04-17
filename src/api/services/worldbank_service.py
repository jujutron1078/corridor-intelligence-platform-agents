"""
World Bank service - serves cached indicator data with live API fallback.
"""

from __future__ import annotations

import logging
from typing import Any

from src.pipelines.worldbank_pipeline.indicators import (
    load_indicators,
    fetch_indicator,
    get_indicator_for_country,
    get_latest_values,
    INDICATORS,
    COUNTRY_NAMES,
)

logger = logging.getLogger("corridor.api.worldbank_service")

_data: dict[str, list[dict]] = {}
_loaded = False


def init() -> None:
    """Load cached World Bank indicator data."""
    global _data, _loaded
    _data = load_indicators()
    if _data:
        total = sum(len(v) for v in _data.values())
        logger.info("World Bank service loaded: %d indicators, %d records", len(_data), total)
    else:
        logger.warning("No World Bank data cached. Run 'python run_all.py pull' to fetch.")
    _loaded = True


def is_loaded() -> bool:
    """Check if data is loaded."""
    return _loaded and bool(_data)


def get_available_indicators() -> list[dict[str, str]]:
    """Return list of available indicator definitions."""
    return [
        {"key": key, "code": info["code"], "name": info["name"], "unit": info["unit"]}
        for key, info in INDICATORS.items()
    ]


def get_indicator(
    indicator_key: str,
    country: str | None = None,
    start_year: int | None = None,
    end_year: int | None = None,
) -> dict[str, Any]:
    """
    Get indicator data. Uses cache with live API fallback.

    Args:
        indicator_key: One of the INDICATORS keys (GDP, FDI, etc.)
        country: Optional ISO3 code filter (NGA, BEN, TGO, GHA, CIV)
        start_year: Optional start year filter
        end_year: Optional end year filter

    Returns dict with metadata + data records.
    """
    indicator_info = INDICATORS.get(indicator_key.upper())
    if not indicator_info:
        return {"error": f"Unknown indicator: {indicator_key}. Available: {list(INDICATORS.keys())}"}

    # Try cached data first
    records = get_indicator_for_country(_data, indicator_key.upper(), country)

    # If no cached data, try live API
    if not records:
        try:
            logger.info("Cache miss for %s - fetching from World Bank API...", indicator_key)
            records = fetch_indicator(
                indicator_info["code"],
                start_year=start_year or 2010,
                end_year=end_year or 2024,
            )
            if country:
                records = [r for r in records if r["country_iso3"] == country.upper()]
        except Exception as exc:
            logger.error("Live API fetch failed for %s: %s", indicator_key, exc)
            records = []

    # Filter by year range
    if start_year:
        records = [r for r in records if r["year"] >= start_year]
    if end_year:
        records = [r for r in records if r["year"] <= end_year]

    return {
        "indicator": indicator_key.upper(),
        "indicator_name": indicator_info["name"],
        "unit": indicator_info["unit"],
        "country": country,
        "total_records": len(records),
        "data": records,
    }


def get_country_summary(country: str | None = None) -> dict[str, Any]:
    """
    Get latest values for all indicators for a country (or all countries).
    """
    summary = {}
    for key in INDICATORS:
        latest = get_latest_values(_data, key)
        if country:
            val = latest.get(country.upper())
            if val:
                summary[key] = val
        else:
            summary[key] = latest

    return {
        "country": country,
        "country_name": COUNTRY_NAMES.get(country.upper(), country) if country else "All corridor countries",
        "indicators": summary,
    }
