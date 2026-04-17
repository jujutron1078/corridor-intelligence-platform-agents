"""
GADM v4 administrative boundaries fetcher.

Download URL pattern: https://geodata.ucanr.edu/geodata/gadm/gadm4.1/json/gadm41_{ISO3}_1.json
Provides Level 1 administrative boundaries for the Abidjan-Lagos corridor countries.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import requests

from src.shared.pipeline.utils import DATA_DIR, ensure_dir, retry

logger = logging.getLogger("corridor.gadm")

# ── Configuration ──────────────────────────────────────────────────────────

BASE_URL = "https://geodata.ucanr.edu/geodata/gadm/gadm4.1/json"

CORRIDOR_COUNTRIES = ["NGA", "BEN", "TGO", "GHA", "CIV"]

COUNTRY_NAMES = {
    "NGA": "Nigeria",
    "BEN": "Benin",
    "TGO": "Togo",
    "GHA": "Ghana",
    "CIV": "Côte d'Ivoire",
}

GADM_DATA_DIR = DATA_DIR / "gadm"

# ── Reference data (fallback when download is unavailable) ────────────────

_seed_cache: dict | None = None


def _load_seed() -> dict:
    """Load seed/reference data from disk (cached after first read)."""
    global _seed_cache
    if _seed_cache is not None:
        return _seed_cache
    path = GADM_DATA_DIR / "admin_regions.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            _seed_cache = json.load(f)
            return _seed_cache
    return {}


# ── API fetch functions ────────────────────────────────────────────────────

def fetch_admin_boundaries(country_iso3: str) -> dict[str, Any]:
    """
    Fetch Level 1 administrative boundaries for a single country from GADM v4.1.

    Returns a GeoJSON FeatureCollection, or a simplified reference fallback
    if the download is unavailable.
    """
    iso = country_iso3.upper()
    if iso not in CORRIDOR_COUNTRIES:
        logger.warning("Country %s is not a corridor country", iso)
        return {"type": "FeatureCollection", "features": []}

    try:
        url = f"{BASE_URL}/gadm41_{iso}_1.json"

        def _do_fetch():
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; CorridorIntelligencePlatform/1.0)',
                'Accept': 'application/json',
            }
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
            return resp.json()

        geojson = retry(_do_fetch, max_retries=1, backoff=1.0)

        if geojson and geojson.get("type") == "FeatureCollection":
            logger.info(
                "Fetched GADM boundaries for %s: %d features",
                iso, len(geojson.get("features", [])),
            )
            return geojson

        logger.warning("Invalid GADM GeoJSON for %s, using reference data", iso)
        return _build_reference_geojson(iso)

    except Exception as exc:
        logger.warning("GADM download failed for %s (%s), using reference data", iso, exc)
        return _build_reference_geojson(iso)


def fetch_all_countries() -> dict[str, Any]:
    """
    Fetch and combine admin boundaries for all corridor countries.

    Returns a single GeoJSON FeatureCollection.
    """
    combined_features = []
    for iso in CORRIDOR_COUNTRIES:
        logger.info("Fetching GADM boundaries for %s...", iso)
        geojson = fetch_admin_boundaries(iso)
        features = geojson.get("features", [])
        for f in features:
            if "properties" not in f:
                f["properties"] = {}
            f["properties"]["country_iso3"] = iso
            f["properties"]["country"] = COUNTRY_NAMES.get(iso, iso)
        combined_features.extend(features)
        logger.info("  %d regions for %s", len(features), iso)

    return {
        "type": "FeatureCollection",
        "features": combined_features,
    }


# ── Helper functions ───────────────────────────────────────────────────────

def _build_reference_geojson(country_iso3: str) -> dict[str, Any]:
    """
    Build a simplified reference GeoJSON FeatureCollection from region names.

    These do not contain real geometry — they use placeholder points — but
    they preserve the region names for agent logic that only needs names.
    """
    regions = _load_seed().get("admin_regions", {}).get(country_iso3, [])
    features = []
    for region in regions:
        features.append({
            "type": "Feature",
            "properties": {
                "NAME_1": region,
                "GID_1": f"{country_iso3}.{region.replace(' ', '_')}",
                "country_iso3": country_iso3,
                "country": COUNTRY_NAMES.get(country_iso3, country_iso3),
                "source": "reference_data",
            },
            "geometry": None,  # placeholder — no real geometry in fallback
        })
    return {
        "type": "FeatureCollection",
        "features": features,
    }


def get_regions_for_country(data: dict[str, Any], country_iso3: str) -> list[str]:
    """
    Extract region names for a given country from a combined GeoJSON FeatureCollection.

    Args:
        data: GeoJSON FeatureCollection (combined or single-country).
        country_iso3: ISO3 country code.

    Returns:
        Sorted list of admin level 1 region names.
    """
    regions = []
    for feature in data.get("features", []):
        props = feature.get("properties", {})
        iso = props.get("country_iso3", props.get("GID_0", ""))
        if iso.upper() == country_iso3.upper():
            name = props.get("NAME_1", props.get("name", ""))
            if name:
                regions.append(name)
    return sorted(regions)


def get_boundary_for_region(data: dict[str, Any], region_name: str) -> dict[str, Any] | None:
    """
    Find and return the GeoJSON Feature for a specific region name.

    Args:
        data: GeoJSON FeatureCollection.
        region_name: Name of the admin level 1 region (case-insensitive).

    Returns:
        GeoJSON Feature dict, or None if not found.
    """
    target = region_name.lower()
    for feature in data.get("features", []):
        props = feature.get("properties", {})
        name = props.get("NAME_1", props.get("name", "")).lower()
        if name == target:
            return feature
    return None


# ── Persistence ────────────────────────────────────────────────────────────

def save_boundaries(data: dict[str, Any], country_iso3: str | None = None) -> Path:
    """
    Save admin boundary data as JSON.

    If country_iso3 is provided, saves to a per-country file.
    Otherwise, saves as the combined file.
    """
    ensure_dir(GADM_DATA_DIR)
    if country_iso3:
        path = GADM_DATA_DIR / f"admin_boundaries_{country_iso3.upper()}.json"
    else:
        path = GADM_DATA_DIR / "admin_boundaries.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info("Saved GADM boundaries: %s (%d features)", path, len(data.get("features", [])))
    return path


def load_boundaries(country_iso3: str | None = None) -> dict[str, Any]:
    """
    Load cached admin boundary data from disk.

    If country_iso3 is provided, loads the per-country file.
    Otherwise, loads the combined file.
    """
    if country_iso3:
        path = GADM_DATA_DIR / f"admin_boundaries_{country_iso3.upper()}.json"
    else:
        path = GADM_DATA_DIR / "admin_boundaries.json"
    if not path.exists():
        return {"type": "FeatureCollection", "features": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
