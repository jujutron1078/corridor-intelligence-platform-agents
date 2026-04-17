"""
Geospatial service — serves GeoJSON layers for dashboard maps.

Loads corridor boundaries, infrastructure features, and cities
from data/geospatial/ and existing pipeline outputs.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from src.shared.pipeline.utils import DATA_DIR

logger = logging.getLogger("corridor.api.geospatial_service")

GEO_DIR = DATA_DIR / "geospatial"
OSM_DIR = DATA_DIR / "osm"
ENERGY_DIR = DATA_DIR / "energy"

_layers: dict[str, dict] = {}
_loaded = False

EMPTY_FC: dict = {"type": "FeatureCollection", "features": []}

# Layers to load: (key, path)
_LAYER_DEFS: list[tuple[str, Any]] = [
    # Boundaries
    ("boundaries_ben", GEO_DIR / "BEN_admin_level1.geojson"),
    ("boundaries_civ", GEO_DIR / "CIV_admin_level1.geojson"),
    ("boundaries_gha", GEO_DIR / "GHA_admin_level1.geojson"),
    ("boundaries_nga", GEO_DIR / "NGA_admin_level1.geojson"),
    ("boundaries_tgo", GEO_DIR / "TGO_admin_level1.geojson"),
    # Cities
    ("cities", GEO_DIR / "major_cities.geojson"),
    # Corridor infrastructure
    ("airports", GEO_DIR / "CORRIDOR_airports.geojson"),
    ("border_crossings", GEO_DIR / "CORRIDOR_border_crossings.geojson"),
    ("power_plants", GEO_DIR / "CORRIDOR_power_plants.geojson"),
    ("industrial_zones", GEO_DIR / "CORRIDOR_industrial_zones.geojson"),
    ("mining_sites", GEO_DIR / "CORRIDOR_mining_sites.geojson"),
    ("railways", GEO_DIR / "CORRIDOR_railways.geojson"),
    ("transmission_lines", GEO_DIR / "CORRIDOR_transmission_lines.geojson"),
    # OSM data (from pipeline)
    ("ports", OSM_DIR / "ports.geojson"),
    # Energy (from pipeline)
    ("energy_plants", ENERGY_DIR / "power_plants.geojson"),
]


def init() -> None:
    """Load all geospatial layers."""
    global _layers, _loaded

    loaded_count = 0
    for key, path in _LAYER_DEFS:
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                _layers[key] = data
                feat_count = len(data.get("features", []))
                logger.info("Loaded %s: %d features", key, feat_count)
                loaded_count += 1
            except Exception as exc:
                logger.warning("Failed to load %s: %s", key, exc)
                _layers[key] = dict(EMPTY_FC)
        else:
            _layers[key] = dict(EMPTY_FC)

    logger.info("Geospatial service loaded: %d/%d layers", loaded_count, len(_LAYER_DEFS))
    _loaded = True


def is_loaded() -> bool:
    return _loaded


def get_layer(name: str) -> dict:
    """Get a single GeoJSON layer by name."""
    return _layers.get(name, EMPTY_FC)


def get_boundaries() -> dict:
    """Get all 5 country boundaries merged into one FeatureCollection."""
    features = []
    for key in ("boundaries_ben", "boundaries_civ", "boundaries_gha", "boundaries_nga", "boundaries_tgo"):
        layer = _layers.get(key, EMPTY_FC)
        features.extend(layer.get("features", []))
    return {"type": "FeatureCollection", "features": features}


def get_infrastructure_layers() -> dict[str, dict]:
    """Get all infrastructure layers for the infrastructure dashboard."""
    return {
        "airports": _layers.get("airports", EMPTY_FC),
        "ports": _layers.get("ports", EMPTY_FC),
        "railways": _layers.get("railways", EMPTY_FC),
        "power_plants": _layers.get("power_plants", EMPTY_FC),
        "transmission_lines": _layers.get("transmission_lines", EMPTY_FC),
        "industrial_zones": _layers.get("industrial_zones", EMPTY_FC),
        "mining_sites": _layers.get("mining_sites", EMPTY_FC),
    }


def get_available_layers() -> list[str]:
    """List all available layer names."""
    return [key for key, layer in _layers.items() if layer.get("features")]
