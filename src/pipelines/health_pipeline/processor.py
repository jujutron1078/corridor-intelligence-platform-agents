"""
HDX Health Facilities processor — convert to GeoJSON, filter to corridor AOI.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from src.shared.pipeline.aoi import BBOX_SOUTH, BBOX_WEST, BBOX_NORTH, BBOX_EAST
from src.shared.pipeline.utils import DATA_DIR, ensure_dir
from src.shared.agents.utils.coords import extract_lon_lat

logger = logging.getLogger("corridor.health")

HEALTH_DATA_DIR = DATA_DIR / "health"


def facilities_to_geojson(all_facilities: dict[str, list[dict]]) -> dict:
    """
    Convert healthsites.io API responses to GeoJSON FeatureCollection.

    Filters to corridor AOI bounding box.
    """
    features = []
    for country_iso, facilities in all_facilities.items():
        for fac in facilities:
            try:
                # healthsites.io returns geometry in different formats
                geom = fac.get("geometry", {})
                if isinstance(geom, dict) and "coordinates" in geom:
                    pt = extract_lon_lat(geom["coordinates"])
                    if pt is None:
                        continue
                    lon, lat = pt
                elif "longitude" in fac and "latitude" in fac:
                    lon = float(fac["longitude"])
                    lat = float(fac["latitude"])
                else:
                    continue

                lon, lat = float(lon), float(lat)

                # Filter to corridor bbox
                if not (BBOX_WEST <= lon <= BBOX_EAST and BBOX_SOUTH <= lat <= BBOX_NORTH):
                    continue

                props = fac.get("properties", fac)
                features.append({
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [lon, lat]},
                    "properties": {
                        "name": str(props.get("name", "")),
                        "facility_type": str(props.get("amenity", props.get("type", ""))),
                        "country_iso3": country_iso,
                        "source": "healthsites.io",
                        "uuid": str(props.get("uuid", "")),
                        "operator": str(props.get("operator", "")) if props.get("operator") else None,
                        "beds": int(props["beds"]) if props.get("beds") and str(props["beds"]).isdigit() else None,
                    },
                })
            except (ValueError, TypeError, KeyError):
                continue

    logger.info("Processed %d health facilities in corridor", len(features))
    return {"type": "FeatureCollection", "features": features}


def save_health_facilities(geojson: dict) -> Path:
    """Save health facilities GeoJSON."""
    ensure_dir(HEALTH_DATA_DIR)
    path = HEALTH_DATA_DIR / "hdx_facilities.geojson"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False)
    logger.info("Saved health facilities: %s (%d features)", path, len(geojson["features"]))
    return path


def load_health_facilities() -> dict:
    """Load cached health facilities GeoJSON."""
    path = HEALTH_DATA_DIR / "hdx_facilities.geojson"
    if not path.exists():
        return {"type": "FeatureCollection", "features": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
