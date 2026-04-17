"""
Mineral service — serves USGS mineral data.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from src.shared.pipeline.utils import DATA_DIR, load_geojson

logger = logging.getLogger("corridor.api.mineral_service")

MINERAL_GEOJSON_DIR = DATA_DIR / "mineral" / "geojson"

# Layers that represent actual mineral/resource sites (not infrastructure)
_MINERAL_LAYER_KEYWORDS = ["mineral", "deposit", "exploration", "resource", "og_province"]
_INFRA_LAYER_KEYWORDS = ["power", "transport", "pipeline", "cities", "boundaries", "river", "lake", "political"]

_data: dict[str, dict] = {}
_infra_data: dict[str, dict] = {}
_economic_anchors: dict | None = None
_loaded = False


def _is_mineral_layer(name: str) -> bool:
    """Check if a layer name represents mineral/resource data."""
    name_lower = name.lower()
    if any(kw in name_lower for kw in _INFRA_LAYER_KEYWORDS):
        return False
    return any(kw in name_lower for kw in _MINERAL_LAYER_KEYWORDS)


def init() -> None:
    """Load all mineral GeoJSON data into memory."""
    global _data, _infra_data, _loaded

    if not MINERAL_GEOJSON_DIR.exists():
        logger.warning("Mineral data directory not found: %s", MINERAL_GEOJSON_DIR)
        _loaded = True
        return

    for path in MINERAL_GEOJSON_DIR.glob("*.geojson"):
        try:
            geojson = load_geojson(path)
            count = len(geojson.get("features", []))
            if _is_mineral_layer(path.stem):
                _data[path.stem] = geojson
                logger.info("Loaded mineral layer %s: %d features", path.stem, count)
            else:
                _infra_data[path.stem] = geojson
                logger.info("Loaded USGS infra layer %s: %d features", path.stem, count)
        except Exception as exc:
            logger.error("Failed to load mineral %s: %s", path.stem, exc)

    _loaded = True


def is_loaded() -> bool:
    """Check if mineral data is loaded."""
    return _loaded


# Large resource province layers that cover entire regions — exclude from map viz
_EXCLUDED_LAYERS = {"afr_og_resources_recoverable", "afr_og_provinces_conventional"}


def get_all_minerals() -> dict:
    """Get all mineral features combined (excludes massive province polygons)."""
    features = []
    for name, data in _data.items():
        if name in _EXCLUDED_LAYERS:
            continue
        for f in data.get("features", []):
            f_copy = dict(f)
            f_copy["properties"] = dict(f_copy.get("properties", {}))
            f_copy["properties"]["source_layer"] = name
            features.append(f_copy)
    return {"type": "FeatureCollection", "features": features}


def get_minerals(commodity: str | None = None, status: str | None = None) -> dict:
    """Get mineral features with optional filtering."""
    all_minerals = get_all_minerals()

    if not commodity and not status:
        return all_minerals

    features = all_minerals["features"]

    if commodity:
        features = [
            f for f in features
            if f["properties"].get("commodity_type", "").lower() == commodity.lower()
        ]

    if status:
        features = [
            f for f in features
            if f["properties"].get("facility_status", "").lower() == status.lower()
        ]

    return {"type": "FeatureCollection", "features": features}


def get_natural_features(feature_type: str | None = None) -> dict:
    """Get natural features (rivers, lakes) from USGS data."""
    features = []
    for name, data in _infra_data.items():
        name_lower = name.lower()
        if feature_type == "rivers" and "river" not in name_lower:
            continue
        if feature_type == "lakes" and "lake" not in name_lower:
            continue
        if feature_type is None and "river" not in name_lower and "lake" not in name_lower:
            continue
        for f in data.get("features", []):
            f_copy = dict(f)
            f_copy["properties"] = dict(f_copy.get("properties", {}))
            f_copy["properties"]["feature_type"] = "river" if "river" in name_lower else "lake"
            features.append(f_copy)
    return {"type": "FeatureCollection", "features": features}


def get_economic_anchors() -> dict:
    """
    Get unified economic anchors layer.
    Combines mineral sites, ports, industrial zones, power plants.
    """
    global _economic_anchors

    if _economic_anchors is not None:
        return _economic_anchors

    # Import OSM service for ports/industrial data
    from src.api.services import osm_service

    minerals = get_all_minerals()
    ports = osm_service.get_ports()
    industrial = osm_service.get_industrial()

    # Find power-related features in USGS infrastructure data
    power_features = []
    for name, data in _infra_data.items():
        if "power" in name.lower() or "electric" in name.lower() or "energy" in name.lower():
            power_features.extend(data.get("features", []))

    power = {"type": "FeatureCollection", "features": power_features}

    from src.pipelines.mineral_pipeline.processor import create_economic_anchors
    _economic_anchors = create_economic_anchors(minerals, ports, industrial, power)
    return _economic_anchors
