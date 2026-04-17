"""
IMF World Economic Outlook data client — macroeconomic indicators for corridor countries.

API docs: https://www.imf.org/external/datamapper/api/v1
No API key required.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import requests

from src.shared.pipeline.utils import DATA_DIR, ensure_dir, retry

logger = logging.getLogger("corridor.imf")

# ── Configuration ──────────────────────────────────────────────────────────

BASE_URL = "https://www.imf.org/external/datamapper/api/v1"

CORRIDOR_COUNTRIES = ["NGA", "BEN", "TGO", "GHA", "CIV"]

# Key WEO indicators for corridor economic analysis
INDICATORS = {
    "NGDP_RPCH": {
        "code": "NGDP_RPCH",
        "name": "Real GDP growth (annual %)",
        "unit": "%",
    },
    "PCPIPCH": {
        "code": "PCPIPCH",
        "name": "Inflation, average consumer prices (annual %)",
        "unit": "%",
    },
    "BCA_NGDPD": {
        "code": "BCA_NGDPD",
        "name": "Current account balance (% of GDP)",
        "unit": "%",
    },
    "GGXWDG_NGDP": {
        "code": "GGXWDG_NGDP",
        "name": "General government gross debt (% of GDP)",
        "unit": "%",
    },
    "LUR": {
        "code": "LUR",
        "name": "Unemployment rate (%)",
        "unit": "%",
    },
    "NGDPDPC": {
        "code": "NGDPDPC",
        "name": "GDP per capita, current prices (USD)",
        "unit": "USD",
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

IMF_DATA_DIR = DATA_DIR / "imf"


# ── API fetch functions ──────────────────────────────────────────────────────

def fetch_indicator(
    indicator_code: str,
    countries: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Fetch a single WEO indicator for the corridor countries.

    Returns a list of {country_iso3, country, year, value} dicts.
    """
    if countries is None:
        countries = CORRIDOR_COUNTRIES

    url = f"{BASE_URL}/{indicator_code}"

    def _do_fetch():
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return resp.json()

    try:
        data = retry(_do_fetch, max_retries=3, backoff=2.0)
    except Exception as exc:
        logger.error("Failed to fetch indicator %s: %s", indicator_code, exc)
        return []

    # IMF DataMapper returns {values: {indicator_code: {country: {year: value}}}}
    if not data or "values" not in data:
        logger.warning("No data returned for indicator %s", indicator_code)
        return []

    indicator_data = data["values"].get(indicator_code, {})

    records = []
    for country_iso3 in countries:
        country_values = indicator_data.get(country_iso3, {})
        for year_str, value in country_values.items():
            try:
                records.append({
                    "country_iso3": country_iso3,
                    "country": COUNTRY_NAMES.get(country_iso3, country_iso3),
                    "year": int(year_str),
                    "value": float(value),
                })
            except (ValueError, TypeError):
                continue

    records.sort(key=lambda r: (r["country_iso3"], r["year"]))
    return records


def fetch_all_indicators() -> dict[str, list[dict]]:
    """
    Fetch all configured WEO indicators for corridor countries.

    Returns {indicator_key: [records]}.
    """
    results = {}
    for key, info in INDICATORS.items():
        logger.info("Fetching %s (%s)...", key, info["name"])
        try:
            records = fetch_indicator(info["code"])
            results[key] = records
            logger.info("  %d records", len(records))
        except Exception as exc:
            logger.error("Failed to fetch %s: %s", key, exc)
            results[key] = []
    return results


# ── Persistence ───────────────────────────────────────────────────────────

def save_indicators(data: dict[str, list[dict]]) -> Path:
    """Save all WEO indicator data as JSON."""
    ensure_dir(IMF_DATA_DIR)
    path = IMF_DATA_DIR / "weo_indicators.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info("Saved IMF WEO indicators: %s", path)
    return path


def load_indicators() -> dict[str, list[dict]]:
    """Load cached WEO indicator data from disk."""
    path = IMF_DATA_DIR / "weo_indicators.json"
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        logger.error("Failed to load IMF indicators: %s", exc)
        return {}


def get_latest_values(
    data: dict[str, list[dict]],
    indicator_key: str,
) -> dict[str, Any]:
    """
    Get the latest available value for each country for an indicator.

    Returns {country_iso3: {year, value, country}}.
    """
    records = data.get(indicator_key, [])
    latest: dict[str, dict] = {}
    for r in records:
        iso = r["country_iso3"]
        if iso not in latest or r["year"] > latest[iso]["year"]:
            latest[iso] = {
                "year": r["year"],
                "value": r["value"],
                "country": r.get("country", COUNTRY_NAMES.get(iso, iso)),
            }
    return latest
