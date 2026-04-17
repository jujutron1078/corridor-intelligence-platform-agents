"""
V-Dem (Varieties of Democracy) governance indicators for corridor countries.

V-Dem provides detailed democracy and governance indices. Since the full dataset
requires a large CSV download (~500MB), this module uses curated reference data
for the corridor countries with recent values.

Source: https://www.v-dem.net/
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from src.shared.pipeline.utils import DATA_DIR, ensure_dir

logger = logging.getLogger("corridor.vdem")

# ── Configuration ──────────────────────────────────────────────────────────

CORRIDOR_COUNTRIES = ["NGA", "BEN", "TGO", "GHA", "CIV"]

# Country ISO3 → name mapping
COUNTRY_NAMES = {
    "NGA": "Nigeria",
    "BEN": "Benin",
    "TGO": "Togo",
    "GHA": "Ghana",
    "CIV": "Côte d'Ivoire",
}

# Key V-Dem governance indicators (all scaled 0–1)
GOVERNANCE_INDICATORS = {
    "v2x_polyarchy": {
        "name": "Electoral Democracy Index",
        "description": "Measures responsiveness of rulers to citizens through electoral competition",
        "scale": "0–1 (higher = more democratic)",
    },
    "v2x_libdem": {
        "name": "Liberal Democracy Index",
        "description": "Measures protection of individual and minority rights against state tyranny",
        "scale": "0–1 (higher = more democratic)",
    },
    "v2x_rule": {
        "name": "Rule of Law Index",
        "description": "Measures extent to which laws are transparent, enforced predictably and equally",
        "scale": "0–1 (higher = stronger rule of law)",
    },
    "v2x_corr": {
        "name": "Political Corruption Index",
        "description": "Measures pervasiveness of political corruption across branches of government",
        "scale": "0–1 (higher = more corrupt)",
    },
    "v2x_civlib": {
        "name": "Civil Liberties Index",
        "description": "Measures respect for personal freedoms, association, expression, and assembly",
        "scale": "0–1 (higher = more civil liberties)",
    },
}

VDEM_DATA_DIR = DATA_DIR / "vdem"

# ── Seed / reference data loader ─────────────────────────────────────────

_seed_cache: dict | None = None


def _load_seed() -> dict:
    """Load seed/reference data from disk (cached after first read)."""
    global _seed_cache
    if _seed_cache is not None:
        return _seed_cache
    path = VDEM_DATA_DIR / "governance_indicators.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            _seed_cache = json.load(f)
            return _seed_cache
    return {}


# ── Data access functions ──────────────────────────────────────────────────

def get_governance_indicators(
    country_iso3: str | None = None,
) -> dict[str, Any]:
    """
    Get V-Dem governance indicators for corridor countries.

    Loads from disk if available, otherwise uses reference data.

    Args:
        country_iso3: Optional ISO3 code to filter for a single country.
                      If None, returns data for all corridor countries.

    Returns:
        Dict keyed by country ISO3 with indicator values, or a single
        country dict if country_iso3 is specified.
    """
    # Try loading from disk first
    try:
        data = load_governance()
        if data:
            if country_iso3:
                country_iso3 = country_iso3.upper()
                return data.get(country_iso3, _load_seed().get("governance", {}).get(country_iso3, {}))
            return data
    except Exception as exc:
        logger.warning("Failed to load V-Dem data from disk: %s", exc)

    # Fall back to reference data
    logger.info("Using V-Dem reference data")
    if country_iso3:
        country_iso3 = country_iso3.upper()
        return _load_seed().get("governance", {}).get(country_iso3, {})
    return dict(_load_seed().get("governance", {}))


def get_indicator_comparison(indicator_key: str) -> list[dict[str, Any]]:
    """
    Compare a single governance indicator across all corridor countries.

    Args:
        indicator_key: V-Dem indicator code (e.g. "v2x_polyarchy").

    Returns:
        List of {country_iso3, country, year, indicator, value} dicts,
        sorted by value (descending for most indicators, ascending for corruption).
    """
    if indicator_key not in GOVERNANCE_INDICATORS:
        logger.error("Unknown V-Dem indicator: %s", indicator_key)
        return []

    data = get_governance_indicators()
    results = []

    for iso3, country_data in data.items():
        indicators = country_data.get("indicators", {})
        value = indicators.get(indicator_key)
        if value is not None:
            results.append({
                "country_iso3": iso3,
                "country": country_data.get("country", COUNTRY_NAMES.get(iso3, iso3)),
                "year": country_data.get("year", 2023),
                "indicator": indicator_key,
                "indicator_name": GOVERNANCE_INDICATORS[indicator_key]["name"],
                "value": value,
            })

    # Sort: ascending for corruption (lower = better), descending for others
    reverse = indicator_key != "v2x_corr"
    results.sort(key=lambda r: r["value"], reverse=reverse)
    return results


# ── Persistence ───────────────────────────────────────────────────────────

def save_governance(data: dict[str, dict]) -> Path:
    """Save governance indicator data as JSON."""
    ensure_dir(VDEM_DATA_DIR)
    path = VDEM_DATA_DIR / "governance.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info("Saved V-Dem governance data: %s", path)
    return path


def load_governance() -> dict[str, dict]:
    """Load cached governance indicator data from disk."""
    path = VDEM_DATA_DIR / "governance.json"
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        logger.error("Failed to load V-Dem governance data: %s", exc)
        return {}


def save_reference_data() -> Path:
    """
    Persist the built-in reference data to disk.

    Useful for initializing the data directory without an API call.
    """
    return save_governance(_load_seed().get("governance", {}))
