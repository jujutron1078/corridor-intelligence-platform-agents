"""
Energy data processor — parse power plant CSV, filter to corridor AOI, export GeoJSON.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd

from src.shared.pipeline.aoi import BBOX_SOUTH, BBOX_WEST, BBOX_NORTH, BBOX_EAST, CORRIDOR
from src.shared.pipeline.utils import DATA_DIR, ensure_dir

logger = logging.getLogger("corridor.energy")

ENERGY_DATA_DIR = DATA_DIR / "energy"

# Corridor country ISO codes
CORRIDOR_COUNTRIES = {"NGA", "BEN", "TGO", "GHA", "CIV"}

# Fuel type classification
FUEL_CATEGORIES = {
    "Solar": "solar",
    "Wind": "wind",
    "Hydro": "hydro",
    "Gas": "gas",
    "Oil": "oil",
    "Coal": "coal",
    "Biomass": "biomass",
    "Nuclear": "nuclear",
    "Geothermal": "geothermal",
    "Waste": "waste",
    "Wave and Tidal": "marine",
    "Storage": "storage",
    "Cogeneration": "cogeneration",
    "Petcoke": "oil",
    "Other": "other",
}


def process_power_plants(csv_path: Path | None = None) -> dict:
    """
    Process Global Power Plant Database CSV.

    Filters to corridor countries + AOI bbox.
    Returns GeoJSON FeatureCollection.
    """
    if csv_path is None:
        csv_path = ENERGY_DATA_DIR / "global_power_plants.csv"

    if not csv_path.exists():
        logger.warning("Power plant CSV not found: %s", csv_path)
        return {"type": "FeatureCollection", "features": []}

    df = pd.read_csv(csv_path, low_memory=False)

    # Filter to corridor countries
    df = df[df["country"].isin(CORRIDOR_COUNTRIES)]

    # Filter to corridor bbox (with small buffer)
    buffer = 0.5
    df = df[
        (df["latitude"] >= BBOX_SOUTH - buffer) &
        (df["latitude"] <= BBOX_NORTH + buffer) &
        (df["longitude"] >= BBOX_WEST - buffer) &
        (df["longitude"] <= BBOX_EAST + buffer)
    ]

    features = []
    for _, row in df.iterrows():
        try:
            lon = float(row["longitude"])
            lat = float(row["latitude"])

            fuel_raw = str(row.get("primary_fuel", "Other"))
            fuel_category = FUEL_CATEGORIES.get(fuel_raw, "other")

            capacity_mw = row.get("capacity_mw")
            if pd.notna(capacity_mw):
                capacity_mw = float(capacity_mw)
            else:
                capacity_mw = None

            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": {
                    "name": str(row.get("name", "")),
                    "gppd_idnr": str(row.get("gppd_idnr", "")),
                    "country": str(row.get("country", "")),
                    "country_long": str(row.get("country_long", "")),
                    "capacity_mw": capacity_mw,
                    "primary_fuel": fuel_raw,
                    "fuel_category": fuel_category,
                    "other_fuel1": str(row.get("other_fuel1", "")) if pd.notna(row.get("other_fuel1")) else None,
                    "commissioning_year": int(row["commissioning_year"]) if pd.notna(row.get("commissioning_year")) else None,
                    "owner": str(row.get("owner", "")) if pd.notna(row.get("owner")) else None,
                    "source": str(row.get("source", "")),
                    "url": str(row.get("url", "")) if pd.notna(row.get("url")) else None,
                },
            })
        except (ValueError, TypeError):
            continue

    logger.info("Processed %d power plants in corridor", len(features))
    return {"type": "FeatureCollection", "features": features}


def get_energy_summary(geojson: dict) -> dict:
    """
    Compute summary statistics from power plant GeoJSON.
    """
    features = geojson.get("features", [])

    total_capacity = 0
    by_fuel: dict[str, dict] = {}
    by_country: dict[str, dict] = {}

    for f in features:
        props = f["properties"]
        cap = props.get("capacity_mw") or 0
        fuel = props.get("fuel_category", "other")
        country = props.get("country", "Unknown")

        total_capacity += cap

        if fuel not in by_fuel:
            by_fuel[fuel] = {"count": 0, "capacity_mw": 0}
        by_fuel[fuel]["count"] += 1
        by_fuel[fuel]["capacity_mw"] += cap

        if country not in by_country:
            by_country[country] = {"count": 0, "capacity_mw": 0}
        by_country[country]["count"] += 1
        by_country[country]["capacity_mw"] += cap

    return {
        "total_plants": len(features),
        "total_capacity_mw": round(total_capacity, 1),
        "by_fuel": by_fuel,
        "by_country": by_country,
    }


def export_power_plants(geojson: dict) -> Path:
    """Save power plants GeoJSON."""
    ensure_dir(ENERGY_DATA_DIR)
    path = ENERGY_DATA_DIR / "power_plants.geojson"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False)
    logger.info("Exported power plants: %s (%d features)", path, len(geojson["features"]))
    return path
