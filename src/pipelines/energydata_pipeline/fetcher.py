"""
energydata.info (World Bank ESMAP) transmission grid data fetcher.

API docs: https://energydata.info/api/3/action/ (CKAN-based, public)
Focuses on existing transmission lines, substations, and electrification data
for the Abidjan-Lagos corridor countries.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import requests

from src.shared.pipeline.utils import DATA_DIR, ensure_dir, retry

logger = logging.getLogger("corridor.energydata")

# ── Configuration ──────────────────────────────────────────────────────────

BASE_URL = "https://energydata.info/api/3/action"

CORRIDOR_COUNTRIES = ["NGA", "BEN", "TGO", "GHA", "CIV"]

COUNTRY_NAMES = {
    "NGA": "Nigeria",
    "BEN": "Benin",
    "TGO": "Togo",
    "GHA": "Ghana",
    "CIV": "Côte d'Ivoire",
}

ENERGYDATA_DIR = DATA_DIR / "energydata"

# ── Seed / reference data (loaded from disk, cached) ─────────────────────

_seed_cache: dict | None = None


def _load_seed() -> dict:
    """Load seed/reference data from disk (cached after first read)."""
    global _seed_cache
    if _seed_cache is not None:
        return _seed_cache
    path = ENERGYDATA_DIR / "transmission_grid.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            _seed_cache = json.load(f)
            return _seed_cache
    return {}


# ── API fetch functions ────────────────────────────────────────────────────

def fetch_transmission_lines(country_iso3: str | None = None) -> list[dict[str, Any]]:
    """
    Fetch transmission line data from energydata.info CKAN API.

    Falls back to REFERENCE_DATA if the API is unavailable.
    Optionally filter by country_iso3.
    """
    try:
        url = f"{BASE_URL}/package_search"
        params = {
            "q": "transmission lines electricity grid",
            "fq": "res_format:GeoJSON",
            "rows": 50,
        }

        def _do_fetch():
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()

        data = retry(_do_fetch, max_retries=2, backoff=2.0)

        results = data.get("result", {}).get("results", [])
        if not results:
            logger.info("No transmission line datasets found via API, using reference data")
            return _filter_by_country(_load_seed().get("transmission_lines", []), country_iso3)

        # Parse CKAN dataset metadata into standardised records
        lines = []
        for dataset in results:
            title = dataset.get("title", "")
            notes = dataset.get("notes", "")
            for tag in dataset.get("tags", []):
                if tag.get("name", "").lower() in ["transmission", "grid", "electricity"]:
                    lines.append({
                        "line_id": dataset.get("id", ""),
                        "name": title,
                        "description": notes[:200] if notes else "",
                        "source": "energydata.info",
                    })
                    break

        if lines:
            logger.info("Fetched %d transmission line datasets from energydata.info", len(lines))
            return lines

        logger.info("API returned no matching transmission data, using reference data")
        return _filter_by_country(_load_seed().get("transmission_lines", []), country_iso3)

    except Exception as exc:
        logger.warning("energydata.info API unavailable (%s), using reference data", exc)
        return _filter_by_country(_load_seed().get("transmission_lines", []), country_iso3)


def fetch_substations(country_iso3: str | None = None) -> list[dict[str, Any]]:
    """
    Fetch substation data from energydata.info CKAN API.

    Falls back to REFERENCE_DATA if the API is unavailable.
    Optionally filter by country_iso3.
    """
    try:
        url = f"{BASE_URL}/package_search"
        params = {
            "q": "substations power electricity",
            "fq": "res_format:GeoJSON",
            "rows": 50,
        }

        def _do_fetch():
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()

        data = retry(_do_fetch, max_retries=2, backoff=2.0)

        results = data.get("result", {}).get("results", [])
        if not results:
            logger.info("No substation datasets found via API, using reference data")
            return _filter_by_country(_load_seed().get("substations", []), country_iso3)

        substations = []
        for dataset in results:
            title = dataset.get("title", "")
            notes = dataset.get("notes", "")
            for tag in dataset.get("tags", []):
                if tag.get("name", "").lower() in ["substation", "power", "electricity"]:
                    substations.append({
                        "substation_id": dataset.get("id", ""),
                        "name": title,
                        "description": notes[:200] if notes else "",
                        "source": "energydata.info",
                    })
                    break

        if substations:
            logger.info("Fetched %d substation datasets from energydata.info", len(substations))
            return substations

        logger.info("API returned no matching substation data, using reference data")
        return _filter_by_country(_load_seed().get("substations", []), country_iso3)

    except Exception as exc:
        logger.warning("energydata.info API unavailable (%s), using reference data", exc)
        return _filter_by_country(_load_seed().get("substations", []), country_iso3)


# ── Helper functions ───────────────────────────────────────────────────────

def _filter_by_country(records: list[dict], country_iso3: str | None) -> list[dict]:
    """Filter a list of records by country_iso3 if provided."""
    if country_iso3:
        return [r for r in records if r.get("country_iso3") == country_iso3.upper()]
    return list(records)


def get_grid_summary(data: dict[str, list[dict]]) -> dict[str, Any]:
    """
    Generate a summary of the grid infrastructure data.

    Args:
        data: dict with "transmission_lines" and "substations" keys.

    Returns:
        Summary dict with total_lines, total_km, by_voltage, by_country, by_status.
    """
    lines = data.get("transmission_lines", [])
    substations = data.get("substations", [])

    total_km = sum(l.get("length_km", 0) for l in lines)

    by_voltage: dict[int, int] = {}
    for l in lines:
        v = l.get("voltage_kv", 0)
        by_voltage[v] = by_voltage.get(v, 0) + 1

    by_country: dict[str, int] = {}
    for l in lines:
        c = l.get("country_iso3", "Unknown")
        by_country[c] = by_country.get(c, 0) + 1

    by_status: dict[str, int] = {}
    for l in lines:
        s = l.get("status", "unknown")
        by_status[s] = by_status.get(s, 0) + 1

    return {
        "total_lines": len(lines),
        "total_substations": len(substations),
        "total_km": round(total_km, 1),
        "by_voltage": dict(sorted(by_voltage.items())),
        "by_country": dict(sorted(by_country.items())),
        "by_status": dict(sorted(by_status.items())),
    }


# ── Persistence ────────────────────────────────────────────────────────────

def save_grid_data(data: dict[str, list[dict]]) -> Path:
    """Save grid infrastructure data as JSON."""
    ensure_dir(ENERGYDATA_DIR)
    path = ENERGYDATA_DIR / "grid_infrastructure.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info("Saved grid infrastructure data: %s", path)
    return path


def load_grid_data() -> dict[str, list[dict]]:
    """Load cached grid infrastructure data from disk."""
    path = ENERGYDATA_DIR / "grid_infrastructure.json"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
