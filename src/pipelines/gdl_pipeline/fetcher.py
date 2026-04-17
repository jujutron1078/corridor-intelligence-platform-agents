"""
Global Data Lab sub-national HDI client — Human Development Index at regional level.

API docs: https://globaldatalab.org/shdi/api/
Public API, no key required (may be rate-limited).
Includes reference data fallback for corridor regions.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import requests

from src.shared.pipeline.utils import DATA_DIR, ensure_dir, retry

logger = logging.getLogger("corridor.gdl")

# ── Configuration ──────────────────────────────────────────────────────────

BASE_URL = "https://globaldatalab.org/shdi/api"

CORRIDOR_COUNTRIES = ["NGA", "BEN", "TGO", "GHA", "CIV"]

# Country ISO3 → name mapping
COUNTRY_NAMES = {
    "NGA": "Nigeria",
    "BEN": "Benin",
    "TGO": "Togo",
    "GHA": "Ghana",
    "CIV": "Côte d'Ivoire",
}

GDL_DATA_DIR = DATA_DIR / "gdl"

# ── Seed / reference data (loaded from disk, cached) ─────────────────────

_seed_cache: dict | None = None


def _load_seed() -> dict:
    """Load seed/reference data from disk (cached after first read)."""
    global _seed_cache
    if _seed_cache is not None:
        return _seed_cache
    path = GDL_DATA_DIR / "subnational_hdi.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            _seed_cache = json.load(f)
            return _seed_cache
    return {}


# ── API fetch functions ──────────────────────────────────────────────────────

def fetch_subnational_hdi(
    country_iso3: str | None = None,
) -> list[dict[str, Any]]:
    """
    Fetch sub-national HDI data for corridor countries.

    Attempts to query the Global Data Lab API. Falls back to reference data
    if the API is unavailable or rate-limited.

    Args:
        country_iso3: Optional ISO3 code. If provided, fetches only that country.
                      If None, fetches all corridor countries.

    Returns:
        List of {country_iso3, country, region, year, hdi,
        education_index, income_index, health_index} dicts.
    """
    countries = [country_iso3.upper()] if country_iso3 else CORRIDOR_COUNTRIES
    all_records = []

    for iso3 in countries:
        try:
            records = _fetch_country_from_api(iso3)
            if records:
                all_records.extend(records)
                continue
        except Exception as exc:
            logger.warning(
                "API fetch failed for %s, using reference data: %s", iso3, exc
            )

        # Fallback to reference data
        records = _get_reference_records(iso3)
        all_records.extend(records)

    logger.info("Fetched %d sub-national HDI records", len(all_records))
    return all_records


def _fetch_country_from_api(country_iso3: str) -> list[dict[str, Any]]:
    """
    Fetch sub-national HDI from the Global Data Lab API for a single country.

    Returns parsed records or empty list on failure.
    """
    url = f"{BASE_URL}/shdi/"
    params = {
        "country": country_iso3,
        "format": "json",
    }

    def _do_fetch():
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()

    data = retry(_do_fetch, max_retries=1, backoff=1.0)

    if not data:
        return []

    records = []
    # GDL API returns list of observations
    if isinstance(data, list):
        for item in data:
            try:
                records.append({
                    "country_iso3": country_iso3,
                    "country": COUNTRY_NAMES.get(country_iso3, country_iso3),
                    "region": item.get("region", item.get("name", "Unknown")),
                    "year": int(item.get("year", 0)),
                    "hdi": float(item.get("shdi", 0)),
                    "education_index": float(item.get("edindex", 0)),
                    "income_index": float(item.get("incindex", 0)),
                    "health_index": float(item.get("healthindex", 0)),
                })
            except (ValueError, TypeError) as exc:
                logger.debug("Skipping malformed record: %s", exc)
                continue

    return records


def _get_reference_records(country_iso3: str) -> list[dict[str, Any]]:
    """
    Extract flat records from reference data for a country.
    """
    country_data = _load_seed().get("subnational_hdi", {}).get(country_iso3.upper(), {})
    if not country_data:
        return []

    records = []
    for region in country_data.get("regions", []):
        records.append({
            "country_iso3": country_data["country_iso3"],
            "country": country_data["country"],
            "region": region["region"],
            "year": country_data["year"],
            "hdi": region["hdi"],
            "education_index": region["education_index"],
            "income_index": region["income_index"],
            "health_index": region["health_index"],
        })
    return records


def fetch_all_countries() -> dict[str, list[dict]]:
    """
    Fetch sub-national HDI for all corridor countries.

    Returns {country_iso3: [region_records]}.
    """
    results = {}
    for iso3 in CORRIDOR_COUNTRIES:
        logger.info("Fetching sub-national HDI for %s...", iso3)
        try:
            records = fetch_subnational_hdi(iso3)
            results[iso3] = records
            logger.info("  %d regions", len(records))
        except Exception as exc:
            logger.error("Failed to fetch HDI for %s: %s", iso3, exc)
            results[iso3] = _get_reference_records(iso3)
    return results


# ── Persistence ───────────────────────────────────────────────────────────

def save_subnational_hdi(data: dict[str, list[dict]]) -> Path:
    """Save sub-national HDI data as JSON."""
    ensure_dir(GDL_DATA_DIR)
    path = GDL_DATA_DIR / "subnational_hdi.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info("Saved sub-national HDI data: %s", path)
    return path


def load_subnational_hdi() -> dict[str, list[dict]]:
    """Load cached sub-national HDI data from disk."""
    path = GDL_DATA_DIR / "subnational_hdi.json"
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        logger.error("Failed to load sub-national HDI data: %s", exc)
        return {}


def get_regions_for_country(
    data: dict[str, list[dict]],
    country_iso3: str,
) -> list[dict]:
    """
    Get sub-national HDI data for a specific country.

    Args:
        data: Full dataset keyed by country ISO3.
        country_iso3: Country ISO3 code.

    Returns:
        List of region dicts with HDI and component indices,
        sorted by HDI descending.
    """
    country_iso3 = country_iso3.upper()
    regions = data.get(country_iso3, [])

    if not regions:
        # Fallback to reference data
        logger.info("Using reference HDI data for %s", country_iso3)
        regions = _get_reference_records(country_iso3)

    # Sort by HDI descending (highest development first)
    regions.sort(key=lambda r: r.get("hdi", 0), reverse=True)
    return regions
