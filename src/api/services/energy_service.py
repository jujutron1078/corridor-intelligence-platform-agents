"""
Energy service — serves power plant and energy infrastructure data.
"""

from __future__ import annotations

import logging
from typing import Any

from src.shared.pipeline.utils import load_geojson, DATA_DIR

logger = logging.getLogger("corridor.api.energy_service")

ENERGY_DATA_DIR = DATA_DIR / "energy"

_plants: dict = {}
_grid: dict = {}
_loaded = False


def init() -> None:
    """Load cached energy data."""
    global _plants, _grid, _loaded

    plants_path = ENERGY_DATA_DIR / "power_plants.geojson"
    if plants_path.exists():
        _plants = load_geojson(plants_path)
        logger.info("Energy service loaded: %d power plants", len(_plants.get("features", [])))
    else:
        logger.warning("No power plant data. Run 'python -m pipelines.energy_pipeline.pipeline pull && process'.")
        _plants = {"type": "FeatureCollection", "features": []}

    grid_path = ENERGY_DATA_DIR / "grid_lines.geojson"
    if grid_path.exists():
        _grid = load_geojson(grid_path)
        logger.info("Grid lines loaded: %d features", len(_grid.get("features", [])))
    else:
        _grid = {"type": "FeatureCollection", "features": []}

    _loaded = True


def is_loaded() -> bool:
    return _loaded and bool(_plants.get("features"))


def get_power_plants(
    fuel: str | None = None,
    country: str | None = None,
    min_capacity_mw: float | None = None,
) -> dict[str, Any]:
    """
    Get power plants, optionally filtered.
    """
    features = _plants.get("features", [])

    if fuel:
        features = [
            f for f in features
            if f["properties"].get("fuel_category", "").lower() == fuel.lower()
            or f["properties"].get("primary_fuel", "").lower() == fuel.lower()
        ]
    if country:
        features = [
            f for f in features
            if f["properties"].get("country", "").upper() == country.upper()
        ]
    if min_capacity_mw is not None:
        features = [
            f for f in features
            if (f["properties"].get("capacity_mw") or 0) >= min_capacity_mw
        ]

    # Summary stats
    total_mw = sum(f["properties"].get("capacity_mw") or 0 for f in features)
    fuel_breakdown: dict[str, int] = {}
    for f in features:
        fc = f["properties"].get("fuel_category", "other")
        fuel_breakdown[fc] = fuel_breakdown.get(fc, 0) + 1

    return {
        "type": "FeatureCollection",
        "features": features,
        "summary": {
            "total_plants": len(features),
            "total_capacity_mw": round(total_mw, 1),
            "by_fuel": fuel_breakdown,
        },
    }


def get_grid() -> dict:
    """Get electricity grid lines GeoJSON."""
    return _grid
