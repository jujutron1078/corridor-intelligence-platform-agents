"""
World Bank Open Data API client — fetch economic indicators for corridor countries.

API docs: https://datahelpdesk.worldbank.org/knowledgebase/articles/889392
No API key required.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import requests

from src.shared.pipeline.utils import DATA_DIR, ensure_dir, retry

logger = logging.getLogger("corridor.worldbank")

# ── Configuration ──────────────────────────────────────────────────────────

BASE_URL = "https://api.worldbank.org/v2"

CORRIDOR_COUNTRIES = "NGA;BEN;TGO;GHA;CIV"

# Key indicators for corridor economic analysis
INDICATORS = {
    "GDP": {
        "code": "NY.GDP.MKTP.CD",
        "name": "GDP (current US$)",
        "unit": "USD",
    },
    "GDP_GROWTH": {
        "code": "NY.GDP.MKTP.KD.ZG",
        "name": "GDP growth (annual %)",
        "unit": "%",
    },
    "GDP_PER_CAPITA": {
        "code": "NY.GDP.PCAP.CD",
        "name": "GDP per capita (current US$)",
        "unit": "USD",
    },
    "FDI": {
        "code": "BX.KLT.DINV.WD.GD.ZS",
        "name": "FDI net inflows (% of GDP)",
        "unit": "%",
    },
    "FDI_ABSOLUTE": {
        "code": "BX.KLT.DINV.CD.WD",
        "name": "FDI net inflows (BoP, current US$)",
        "unit": "USD",
    },
    "TRADE_PCT_GDP": {
        "code": "NE.TRD.GNFS.ZS",
        "name": "Trade (% of GDP)",
        "unit": "%",
    },
    "REMITTANCES": {
        "code": "BX.TRF.PWKR.CD.DT",
        "name": "Personal remittances received (current US$)",
        "unit": "USD",
    },
    "EASE_OF_BUSINESS": {
        "code": "IC.BUS.EASE.XQ",
        "name": "Ease of doing business score",
        "unit": "score",
    },
    "INFLATION": {
        "code": "FP.CPI.TOTL.ZG",
        "name": "Inflation, consumer prices (annual %)",
        "unit": "%",
    },
    "POPULATION": {
        "code": "SP.POP.TOTL",
        "name": "Population, total",
        "unit": "people",
    },
    "URBAN_POP_PCT": {
        "code": "SP.URB.TOTL.IN.ZS",
        "name": "Urban population (% of total)",
        "unit": "%",
    },
    "ELECTRICITY_ACCESS": {
        "code": "EG.ELC.ACCS.ZS",
        "name": "Access to electricity (% of population)",
        "unit": "%",
    },
    "INTERNET_USERS": {
        "code": "IT.NET.USER.ZS",
        "name": "Individuals using the Internet (% of population)",
        "unit": "%",
    },
}

# Country ISO3 → name mapping
COUNTRY_NAMES = {
    "NGA": "Nigeria",
    "BEN": "Benin",
    "TGO": "Togo",
    "GHA": "Ghana",
    "CIV": "Côte d'Ivoire",
}

WORLDBANK_DATA_DIR = DATA_DIR / "worldbank"


# ── API fetch functions ──────────────────────────────────────────────────────

def fetch_indicator(
    indicator_code: str,
    countries: str = CORRIDOR_COUNTRIES,
    start_year: int = 2010,
    end_year: int = 2024,
    per_page: int = 500,
) -> list[dict[str, Any]]:
    """
    Fetch a single indicator for the corridor countries.

    Returns a list of {country, country_iso3, year, value} dicts.
    """
    url = f"{BASE_URL}/country/{countries}/indicator/{indicator_code}"
    params = {
        "format": "json",
        "date": f"{start_year}:{end_year}",
        "per_page": per_page,
    }

    def _do_fetch():
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    data = retry(_do_fetch, max_retries=3, backoff=2.0)

    # World Bank returns [metadata, data_array]
    if not data or len(data) < 2 or data[1] is None:
        logger.warning("No data returned for indicator %s", indicator_code)
        return []

    records = []
    for item in data[1]:
        value = item.get("value")
        if value is not None:
            records.append({
                "country": item["country"]["value"],
                "country_iso3": item["countryiso3code"],
                "year": int(item["date"]),
                "value": float(value),
            })

    records.sort(key=lambda r: (r["country_iso3"], r["year"]))
    return records


def fetch_all_indicators(
    start_year: int = 2010,
    end_year: int = 2024,
) -> dict[str, list[dict]]:
    """
    Fetch all configured indicators for corridor countries.

    Returns {indicator_key: [records]}.
    """
    results = {}
    for key, info in INDICATORS.items():
        logger.info("Fetching %s (%s)...", key, info["code"])
        try:
            records = fetch_indicator(info["code"], start_year=start_year, end_year=end_year)
            results[key] = records
            logger.info("  %d records", len(records))
        except Exception as exc:
            logger.error("Failed to fetch %s: %s", key, exc)
            results[key] = []
    return results


# ── Persistence ───────────────────────────────────────────────────────────

def save_indicators(data: dict[str, list[dict]]) -> Path:
    """Save all indicator data as JSON."""
    ensure_dir(WORLDBANK_DATA_DIR)
    path = WORLDBANK_DATA_DIR / "indicators.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info("Saved World Bank indicators: %s", path)
    return path


def load_indicators() -> dict[str, list[dict]]:
    """Load cached indicator data from disk."""
    path = WORLDBANK_DATA_DIR / "indicators.json"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_indicator_for_country(
    data: dict[str, list[dict]],
    indicator_key: str,
    country_iso3: str | None = None,
) -> list[dict]:
    """
    Filter cached indicator data by key and optional country.
    """
    records = data.get(indicator_key, [])
    if country_iso3:
        records = [r for r in records if r["country_iso3"] == country_iso3.upper()]
    return records


def get_latest_values(data: dict[str, list[dict]], indicator_key: str) -> dict[str, Any]:
    """
    Get the latest available value for each country for an indicator.

    Returns {country_iso3: {year, value, country_name}}.
    """
    records = data.get(indicator_key, [])
    latest: dict[str, dict] = {}
    for r in records:
        iso = r["country_iso3"]
        if iso not in latest or r["year"] > latest[iso]["year"]:
            latest[iso] = {
                "year": r["year"],
                "value": r["value"],
                "country": r["country"],
            }
    return latest
