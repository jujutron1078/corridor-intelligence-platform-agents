"""
Overpass API data extraction with rate limiting and retry logic.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import requests

from src.shared.pipeline.utils import RateLimiter, retry
from .config import (
    OVERPASS_URL, OVERPASS_TIMEOUT, OVERPASS_BBOX,
    QUERIES, RATE_LIMIT_CALLS, RATE_LIMIT_PERIOD,
)

logger = logging.getLogger("corridor.osm.extractor")

_rate_limiter = RateLimiter(max_calls=RATE_LIMIT_CALLS, period_seconds=RATE_LIMIT_PERIOD)


def _query_overpass(query_template: str) -> dict[str, Any]:
    """
    Send a query to the Overpass API with rate limiting and retries.

    Returns the raw JSON response.
    """
    query = query_template.format(timeout=OVERPASS_TIMEOUT, bbox=OVERPASS_BBOX)

    def _do_request():
        _rate_limiter.wait()
        logger.debug("Sending Overpass query (%d chars)", len(query))
        resp = requests.post(
            OVERPASS_URL,
            data={"data": query},
            timeout=OVERPASS_TIMEOUT + 30,
        )
        resp.raise_for_status()
        return resp.json()

    return retry(
        _do_request,
        max_retries=3,
        backoff=30.0,
        exceptions=(requests.RequestException, requests.Timeout),
    )


def _elements_to_nodes(elements: list[dict]) -> dict[int, dict]:
    """Index all node elements by ID for way coordinate resolution."""
    return {
        e["id"]: e
        for e in elements
        if e["type"] == "node" and "lat" in e and "lon" in e
    }


def _resolve_way_coords(way: dict, nodes: dict[int, dict]) -> list[list[float]]:
    """Resolve a way's node references to [lon, lat] coordinate pairs."""
    coords = []
    for node_id in way.get("nodes", []):
        node = nodes.get(node_id)
        if node:
            coords.append([node["lon"], node["lat"]])
    return coords


def _to_geojson_features(elements: list[dict]) -> list[dict]:
    """
    Convert Overpass elements to GeoJSON features.

    Handles nodes (Point), ways (LineString/Polygon).
    """
    nodes = _elements_to_nodes(elements)
    features = []

    for el in elements:
        props = dict(el.get("tags", {}))
        props["osm_id"] = el["id"]
        props["osm_type"] = el["type"]

        if el["type"] == "node" and "lat" in el and "lon" in el:
            # Skip nodes that are just part of ways (no tags)
            if not el.get("tags"):
                continue
            features.append({
                "type": "Feature",
                "properties": props,
                "geometry": {
                    "type": "Point",
                    "coordinates": [el["lon"], el["lat"]],
                },
            })

        elif el["type"] == "way":
            coords = _resolve_way_coords(el, nodes)
            if len(coords) < 2:
                continue

            # If first == last coord and ≥4 coords, it's a polygon
            if len(coords) >= 4 and coords[0] == coords[-1]:
                geom_type = "Polygon"
                coordinates = [coords]
            else:
                geom_type = "LineString"
                coordinates = coords

            features.append({
                "type": "Feature",
                "properties": props,
                "geometry": {
                    "type": geom_type,
                    "coordinates": coordinates,
                },
            })

    return features


def extract_roads() -> dict:
    """Extract all road data from OSM. Returns GeoJSON FeatureCollection."""
    logger.info("Extracting roads from OSM...")
    data = _query_overpass(QUERIES["roads"])
    features = _to_geojson_features(data.get("elements", []))
    logger.info("Extracted %d road features", len(features))
    return {"type": "FeatureCollection", "features": features}


def extract_railways() -> dict:
    """Extract railway lines. Returns GeoJSON FeatureCollection."""
    logger.info("Extracting railways from OSM...")
    data = _query_overpass(QUERIES["railways"])
    features = _to_geojson_features(data.get("elements", []))
    logger.info("Extracted %d railway features", len(features))
    return {"type": "FeatureCollection", "features": features}


def extract_ports() -> dict:
    """Extract ports and harbors. Returns GeoJSON FeatureCollection."""
    logger.info("Extracting ports from OSM...")
    data = _query_overpass(QUERIES["ports"])
    features = _to_geojson_features(data.get("elements", []))
    logger.info("Extracted %d port features", len(features))
    return {"type": "FeatureCollection", "features": features}


def extract_airports() -> dict:
    """Extract airports. Returns GeoJSON FeatureCollection."""
    logger.info("Extracting airports from OSM...")
    data = _query_overpass(QUERIES["airports"])
    features = _to_geojson_features(data.get("elements", []))
    logger.info("Extracted %d airport features", len(features))
    return {"type": "FeatureCollection", "features": features}


def extract_industrial() -> dict:
    """Extract industrial areas. Returns GeoJSON FeatureCollection."""
    logger.info("Extracting industrial areas from OSM...")
    data = _query_overpass(QUERIES["industrial"])
    features = _to_geojson_features(data.get("elements", []))
    logger.info("Extracted %d industrial features", len(features))
    return {"type": "FeatureCollection", "features": features}


def extract_sez_ftz() -> dict:
    """Extract SEZs / free trade zones. Returns GeoJSON FeatureCollection."""
    logger.info("Extracting SEZ/FTZ from OSM...")
    data = _query_overpass(QUERIES["sez_ftz"])
    features = _to_geojson_features(data.get("elements", []))
    logger.info("Extracted %d SEZ/FTZ features", len(features))
    return {"type": "FeatureCollection", "features": features}


def extract_border_crossings() -> dict:
    """Extract border crossings. Returns GeoJSON FeatureCollection."""
    logger.info("Extracting border crossings from OSM...")
    data = _query_overpass(QUERIES["border_crossings"])
    features = _to_geojson_features(data.get("elements", []))
    logger.info("Extracted %d border crossing features", len(features))
    return {"type": "FeatureCollection", "features": features}


def extract_pois() -> dict:
    """Extract key POIs (fuel, markets, warehouses, customs). Returns GeoJSON FeatureCollection."""
    logger.info("Extracting POIs from OSM...")
    data = _query_overpass(QUERIES["pois"])
    features = _to_geojson_features(data.get("elements", []))
    logger.info("Extracted %d POI features", len(features))
    return {"type": "FeatureCollection", "features": features}


def extract_health() -> dict:
    """Extract health facilities (hospitals, clinics, pharmacies). Returns GeoJSON FeatureCollection."""
    logger.info("Extracting health facilities from OSM...")
    data = _query_overpass(QUERIES["health"])
    features = _to_geojson_features(data.get("elements", []))
    logger.info("Extracted %d health features", len(features))
    return {"type": "FeatureCollection", "features": features}


def extract_education() -> dict:
    """Extract education facilities (schools, universities, libraries). Returns GeoJSON FeatureCollection."""
    logger.info("Extracting education facilities from OSM...")
    data = _query_overpass(QUERIES["education"])
    features = _to_geojson_features(data.get("elements", []))
    logger.info("Extracted %d education features", len(features))
    return {"type": "FeatureCollection", "features": features}


def extract_government() -> dict:
    """Extract government facilities (police, fire, courts, post offices). Returns GeoJSON FeatureCollection."""
    logger.info("Extracting government facilities from OSM...")
    data = _query_overpass(QUERIES["government"])
    features = _to_geojson_features(data.get("elements", []))
    logger.info("Extracted %d government features", len(features))
    return {"type": "FeatureCollection", "features": features}


def extract_financial() -> dict:
    """Extract financial services (banks, ATMs, bureaux de change). Returns GeoJSON FeatureCollection."""
    logger.info("Extracting financial services from OSM...")
    data = _query_overpass(QUERIES["financial"])
    features = _to_geojson_features(data.get("elements", []))
    logger.info("Extracted %d financial features", len(features))
    return {"type": "FeatureCollection", "features": features}


def extract_religious() -> dict:
    """Extract places of worship. Returns GeoJSON FeatureCollection."""
    logger.info("Extracting places of worship from OSM...")
    data = _query_overpass(QUERIES["religious"])
    features = _to_geojson_features(data.get("elements", []))
    logger.info("Extracted %d religious features", len(features))
    return {"type": "FeatureCollection", "features": features}


def extract_all() -> dict[str, dict]:
    """
    Extract all feature types.

    Returns: {"roads": GeoJSON, "railways": GeoJSON, ...}
    """
    extractors = {
        "roads": extract_roads,
        "railways": extract_railways,
        "ports": extract_ports,
        "airports": extract_airports,
        "industrial": extract_industrial,
        "sez_ftz": extract_sez_ftz,
        "border_crossings": extract_border_crossings,
        "pois": extract_pois,
        "health": extract_health,
        "education": extract_education,
        "government": extract_government,
        "financial": extract_financial,
        "religious": extract_religious,
    }

    results = {}
    for name, fn in extractors.items():
        try:
            results[name] = fn()
        except Exception as exc:
            logger.error("Failed to extract %s: %s", name, exc)
            results[name] = {"type": "FeatureCollection", "features": []}

    return results
