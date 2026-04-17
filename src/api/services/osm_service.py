"""
OSM service — serves pre-processed OSM GeoJSON data.
"""

from __future__ import annotations

import logging
from typing import Any

from src.api.cache import data_cache, make_cache_key
from src.pipelines.osm_pipeline.config import OSM_OUTPUT_FILES
from src.pipelines.osm_pipeline.processor import filter_roads_by_tier
from src.shared.pipeline.utils import load_geojson, DATA_DIR

logger = logging.getLogger("corridor.api.osm_service")

# In-memory data store (loaded on startup)
_data: dict[str, dict] = {}
_network_stats: dict[str, Any] = {}
_loaded = False


def init() -> None:
    """Load all OSM data into memory."""
    global _data, _network_stats, _loaded

    for name, path in OSM_OUTPUT_FILES.items():
        if not path.exists():
            logger.warning("OSM data file not found: %s", path)
            continue

        try:
            _data[name] = load_geojson(path)
            count = len(_data[name].get("features", []))
            logger.info("Loaded OSM %s: %d features", name, count)
        except Exception as exc:
            logger.error("Failed to load OSM %s: %s", name, exc)

    # Load network stats
    network_path = OSM_OUTPUT_FILES.get("network")
    if network_path and network_path.exists():
        import json
        with open(network_path) as f:
            _network_stats = json.load(f)
        logger.info("Loaded network statistics")

    # Load HDX health facilities alongside OSM health data
    hdx_path = DATA_DIR / "health" / "hdx_facilities.geojson"
    if hdx_path.exists():
        try:
            hdx = load_geojson(hdx_path)
            count = len(hdx.get("features", []))
            _data["hdx_health"] = hdx
            logger.info("Loaded HDX health facilities: %d features", count)
        except Exception as exc:
            logger.error("Failed to load HDX health data: %s", exc)

    _loaded = True


def is_loaded() -> bool:
    """Check if OSM data is loaded."""
    return _loaded


def get_roads(tiers: list[int] | None = None) -> dict:
    """Get road network GeoJSON, optionally filtered by tier."""
    roads = _data.get("roads", {"type": "FeatureCollection", "features": []})
    if tiers:
        return filter_roads_by_tier(roads, tiers)
    return roads


def get_roads_by_highway(types: list[str]) -> dict:
    """Get road network filtered by OSM highway types (motorway, trunk, primary, etc.)."""
    roads = _data.get("roads", {"type": "FeatureCollection", "features": []})
    # Also match *_link variants (e.g. motorway_link)
    expanded = set()
    for t in types:
        expanded.add(t)
        expanded.add(f"{t}_link")
    features = [
        f for f in roads.get("features", [])
        if f.get("properties", {}).get("highway", "").lower() in expanded
    ]
    return {"type": "FeatureCollection", "features": features}


def get_railways() -> dict:
    """Get railway GeoJSON."""
    return _data.get("railways", {"type": "FeatureCollection", "features": []})


def get_ports() -> dict:
    """Get ports/harbors GeoJSON."""
    return _data.get("ports", {"type": "FeatureCollection", "features": []})


def get_airports() -> dict:
    """Get airports GeoJSON."""
    return _data.get("airports", {"type": "FeatureCollection", "features": []})


def get_industrial() -> dict:
    """Get industrial areas GeoJSON."""
    return _data.get("industrial", {"type": "FeatureCollection", "features": []})


def get_border_crossings() -> dict:
    """Get border crossings GeoJSON."""
    return _data.get("border_crossings", {"type": "FeatureCollection", "features": []})


def get_infrastructure() -> dict:
    """Get all infrastructure GeoJSON (ports, airports, rail, borders, industrial, SEZ)."""
    features = []
    for layer in ["ports", "airports", "railways", "border_crossings", "industrial", "sez_ftz"]:
        data = _data.get(layer, {})
        for f in data.get("features", []):
            f_copy = dict(f)
            f_copy["properties"] = dict(f_copy.get("properties", {}))
            f_copy["properties"]["infrastructure_type"] = layer
            features.append(f_copy)
    return {"type": "FeatureCollection", "features": features}


def get_social_facilities(facility_type: str | None = None) -> dict:
    """Get social infrastructure GeoJSON (health, education, government, financial, religious, military, recreational)."""
    social_layers = ["health", "education", "government", "financial", "religious", "military", "recreational", "pois"]
    features = []
    for layer in social_layers:
        if facility_type and layer != facility_type:
            continue
        data = _data.get(layer, {})
        for f in data.get("features", []):
            f_copy = dict(f)
            f_copy["properties"] = dict(f_copy.get("properties", {}))
            f_copy["properties"]["facility_type"] = layer
            features.append(f_copy)
    return {"type": "FeatureCollection", "features": features}


def get_network_stats() -> dict:
    """Get road network connectivity metrics."""
    return _network_stats
