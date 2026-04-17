"""
FAO FAOSTAT agricultural production data - key commodities for corridor countries.

API docs: https://fenixservices.fao.org/faostat/api/v1/
No API key required.

Covers cocoa, palm oil, cashew, rubber, yams, cassava, maize, and rice
production across Nigeria, Benin, Togo, Ghana, and Côte d'Ivoire.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import requests

from src.shared.pipeline.utils import DATA_DIR, ensure_dir, retry

logger = logging.getLogger("corridor.fao")

# -- Configuration -----------------------------------------------------------

BASE_URL = "https://fenixservices.fao.org/faostat/api/v1"

FAO_DATA_DIR = DATA_DIR / "fao"

# FAO area codes for corridor countries
CORRIDOR_COUNTRIES = {
    "NGA": {"fao_code": 159, "name": "Nigeria"},
    "BEN": {"fao_code": 53, "name": "Benin"},
    "TGO": {"fao_code": 217, "name": "Togo"},
    "GHA": {"fao_code": 81, "name": "Ghana"},
    "CIV": {"fao_code": 107, "name": "Côte d'Ivoire"},
}

# Key agricultural commodities and their FAO item codes
KEY_COMMODITIES = {
    "cocoa": {"code": 661, "name": "Cocoa beans"},
    "palm_oil": {"code": 254, "name": "Oil palm fruit"},
    "cashew": {"code": 217, "name": "Cashew nuts, in shell"},
    "rubber": {"code": 836, "name": "Natural rubber"},
    "yams": {"code": 116, "name": "Yams"},
    "cassava": {"code": 125, "name": "Cassava, fresh"},
    "maize": {"code": 56, "name": "Maize (corn)"},
    "rice": {"code": 27, "name": "Rice, paddy"},
}

# -- Seed / reference data (loaded from disk, cached) -------------------------

_seed_cache: dict | None = None


def _load_seed() -> dict:
    """Load seed/reference data from disk (cached after first read)."""
    global _seed_cache
    if _seed_cache is not None:
        return _seed_cache
    path = FAO_DATA_DIR / "agricultural_production.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            _seed_cache = json.load(f)
            return _seed_cache
    return {}


# -- API fetch functions -------------------------------------------------------

def fetch_production(
    commodity_code: int,
    countries: dict[str, dict] | None = None,
) -> list[dict[str, Any]]:
    """
    Fetch production data for a commodity from FAOSTAT API.

    Falls back to reference data if the API is unavailable.

    Returns a list of {country_iso3, commodity, year, production_tonnes,
    area_harvested_ha, yield_kg_per_ha} dicts.
    """
    if countries is None:
        countries = CORRIDOR_COUNTRIES

    # Find commodity name from code
    commodity_name = "unknown"
    for name, info in KEY_COMMODITIES.items():
        if info["code"] == commodity_code:
            commodity_name = name
            break

    area_codes = ",".join(str(c["fao_code"]) for c in countries.values())

    url = f"{BASE_URL}/en/data/QCL"
    params = {
        "area": area_codes,
        "item": str(commodity_code),
        "element": "5510,5312,5419",  # Production, Area, Yield
        "year": "2018,2019,2020,2021,2022,2023",
        "output_type": "objects",
    }

    try:
        def _do_fetch():
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()

        raw = retry(_do_fetch, max_retries=1, backoff=1.0)

        # Parse FAOSTAT response
        if raw and "data" in raw:
            return _parse_faostat_response(raw["data"], commodity_name, countries)
        else:
            logger.warning("No data from FAOSTAT for commodity %s, using reference data", commodity_code)
            return _reference_fallback(commodity_name, countries)

    except Exception as exc:
        logger.warning("FAOSTAT API failed for commodity %s: %s - using reference data", commodity_code, exc)
        return _reference_fallback(commodity_name, countries)


def _parse_faostat_response(
    data: list[dict],
    commodity_name: str,
    countries: dict[str, dict],
) -> list[dict[str, Any]]:
    """Parse raw FAOSTAT API response into clean records."""
    # Build reverse lookup: fao_code -> iso3
    fao_to_iso = {v["fao_code"]: k for k, v in countries.items()}

    # Group by country+year
    grouped: dict[tuple[int, int], dict] = {}
    for item in data:
        area_code = item.get("Area Code")
        year = item.get("Year")
        element = item.get("Element")
        value = item.get("Value")

        if area_code is None or year is None or value is None:
            continue

        key = (area_code, year)
        if key not in grouped:
            grouped[key] = {"area_code": area_code, "year": year}

        if element == "Production":
            grouped[key]["production_tonnes"] = float(value)
        elif element == "Area harvested":
            grouped[key]["area_harvested_ha"] = float(value)
        elif element == "Yield":
            grouped[key]["yield_kg_per_ha"] = float(value)

    records = []
    for (area_code, year), vals in grouped.items():
        iso3 = fao_to_iso.get(area_code)
        if iso3:
            records.append({
                "country_iso3": iso3,
                "commodity": commodity_name,
                "year": year,
                "production_tonnes": vals.get("production_tonnes", 0),
                "area_harvested_ha": vals.get("area_harvested_ha", 0),
                "yield_kg_per_ha": vals.get("yield_kg_per_ha", 0),
            })

    records.sort(key=lambda r: (r["country_iso3"], r["year"]))
    return records


def _reference_fallback(
    commodity_name: str,
    countries: dict[str, dict],
) -> list[dict[str, Any]]:
    """Return reference data as fallback when API is unavailable."""
    commodity_data = _load_seed().get("production", {}).get(commodity_name, {})
    records = []
    for iso3 in countries:
        if iso3 in commodity_data:
            entry = commodity_data[iso3]
            records.append({
                "country_iso3": iso3,
                "commodity": commodity_name,
                "year": entry["year"],
                "production_tonnes": entry["production_tonnes"],
                "area_harvested_ha": entry["area_harvested_ha"],
                "yield_kg_per_ha": entry["yield_kg_per_ha"],
            })
    records.sort(key=lambda r: (r["country_iso3"], r["year"]))
    return records


def fetch_all_commodities() -> dict[str, list[dict[str, Any]]]:
    """
    Fetch production data for all key commodities.

    Returns {commodity_name: [records]}.
    """
    results = {}
    for name, info in KEY_COMMODITIES.items():
        logger.info("Fetching FAO production data: %s (%d)...", name, info["code"])
        try:
            records = fetch_production(info["code"])
            results[name] = records
            logger.info("  %d records", len(records))
        except Exception as exc:
            logger.error("Failed to fetch %s: %s", name, exc)
            results[name] = _reference_fallback(name, CORRIDOR_COUNTRIES)
    return results


# -- Persistence --------------------------------------------------------------

def save_production(data: dict[str, list[dict]]) -> Path:
    """Save all production data as JSON."""
    ensure_dir(FAO_DATA_DIR)
    path = FAO_DATA_DIR / "production.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info("Saved FAO production data: %s", path)
    return path


def load_production() -> dict[str, list[dict]]:
    """Load cached production data from disk."""
    path = FAO_DATA_DIR / "production.json"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# -- Query helpers ------------------------------------------------------------

def get_production_by_country(
    data: dict[str, list[dict]],
    country_iso3: str,
) -> dict[str, list[dict]]:
    """
    Filter all commodity data for a specific country.

    Returns {commodity_name: [records for that country]}.
    """
    result = {}
    for commodity, records in data.items():
        filtered = [r for r in records if r["country_iso3"] == country_iso3.upper()]
        if filtered:
            result[commodity] = filtered
    return result
