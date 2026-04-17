"""
OSM data processor — road classification, network graph, connectivity metrics.
"""

from __future__ import annotations

import json
import logging
import math
from typing import Any

import networkx as nx

from .config import HIGHWAY_TO_TIER, ROAD_TIERS
from src.shared.pipeline.aoi import CORRIDOR_NODES

logger = logging.getLogger("corridor.osm.processor")


def _haversine(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Haversine distance in km between two (lon, lat) points."""
    R = 6371.0
    rlat1, rlat2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _line_length_km(coords: list[list[float]]) -> float:
    """Total length of a linestring in km."""
    total = 0.0
    for i in range(len(coords) - 1):
        total += _haversine(coords[i][0], coords[i][1], coords[i + 1][0], coords[i + 1][1])
    return total


def classify_roads(roads_geojson: dict) -> dict:
    """
    Add tier, surface, and length_km to each road feature.

    Modifies the GeoJSON in-place and returns it.
    """
    for feature in roads_geojson.get("features", []):
        props = feature["properties"]
        highway = props.get("highway", "")
        props["tier"] = HIGHWAY_TO_TIER.get(highway, 4)
        props["surface"] = props.get("surface", "unknown")

        geom = feature.get("geometry", {})
        if geom.get("type") == "LineString":
            props["length_km"] = round(_line_length_km(geom["coordinates"]), 3)
        else:
            props["length_km"] = 0.0

    return roads_geojson


def filter_roads_by_tier(roads_geojson: dict, tiers: list[int] | None = None) -> dict:
    """Filter road features to specific tiers."""
    if tiers is None:
        return roads_geojson

    features = [
        f for f in roads_geojson.get("features", [])
        if f["properties"].get("tier") in tiers
    ]
    return {"type": "FeatureCollection", "features": features}


def build_network_graph(roads_geojson: dict) -> nx.Graph:
    """
    Build a NetworkX graph from the road GeoJSON.

    Nodes = unique coordinate points (rounded to ~10m precision).
    Edges = road segments with length, type, surface, tier.
    """
    G = nx.Graph()

    def _round_coord(lon: float, lat: float) -> tuple[float, float]:
        return (round(lon, 4), round(lat, 4))

    for feature in roads_geojson.get("features", []):
        geom = feature.get("geometry", {})
        if geom.get("type") != "LineString":
            continue

        coords = geom["coordinates"]
        props = feature["properties"]
        tier = props.get("tier", 4)
        highway = props.get("highway", "unknown")
        surface = props.get("surface", "unknown")

        for i in range(len(coords) - 1):
            u = _round_coord(coords[i][0], coords[i][1])
            v = _round_coord(coords[i + 1][0], coords[i + 1][1])

            length = _haversine(coords[i][0], coords[i][1], coords[i + 1][0], coords[i + 1][1])

            G.add_node(u, lon=u[0], lat=u[1])
            G.add_node(v, lon=v[0], lat=v[1])

            G.add_edge(u, v, length_km=length, highway=highway, surface=surface, tier=tier)

    logger.info("Built network graph: %d nodes, %d edges", G.number_of_nodes(), G.number_of_edges())
    return G


def compute_network_stats(G: nx.Graph) -> dict[str, Any]:
    """Compute connectivity metrics for the road network."""
    stats = {
        "total_nodes": G.number_of_nodes(),
        "total_edges": G.number_of_edges(),
        "total_km": round(sum(d.get("length_km", 0) for _, _, d in G.edges(data=True)), 1),
        "km_by_tier": {},
        "connected_components": nx.number_connected_components(G),
        "largest_component_size": 0,
    }

    # km by tier
    for tier in [1, 2, 3, 4]:
        tier_km = sum(
            d.get("length_km", 0)
            for _, _, d in G.edges(data=True)
            if d.get("tier") == tier
        )
        stats["km_by_tier"][f"tier_{tier}"] = round(tier_km, 1)

    # Largest connected component
    if G.number_of_nodes() > 0:
        components = sorted(nx.connected_components(G), key=len, reverse=True)
        stats["largest_component_size"] = len(components[0]) if components else 0

    return stats


def find_pinch_points(G: nx.Graph) -> list[dict]:
    """
    Identify corridor pinch points — nodes whose removal would disconnect
    the graph between major cities.

    Uses articulation point detection.
    """
    if G.number_of_nodes() == 0:
        return []

    # Get the largest connected component for analysis
    largest_cc = max(nx.connected_components(G), key=len)
    subgraph = G.subgraph(largest_cc).copy()

    # Find articulation points (cut vertices)
    try:
        art_points = list(nx.articulation_points(subgraph))
    except nx.NetworkXError:
        return []

    # Filter to points near corridor nodes (within ~5km)
    corridor_coords = [(n["lon"], n["lat"]) for n in CORRIDOR_NODES]
    significant = []

    for point in art_points:
        lon, lat = point
        for node in CORRIDOR_NODES:
            dist = _haversine(lon, lat, node["lon"], node["lat"])
            if dist < 50:  # within 50km of a corridor node
                degree = subgraph.degree(point)
                if degree >= 2:  # meaningful junction
                    significant.append({
                        "lon": lon,
                        "lat": lat,
                        "degree": degree,
                        "nearest_node": node["name"],
                        "distance_km": round(dist, 1),
                    })
                break

    # Sort by degree (higher = more critical)
    significant.sort(key=lambda x: x["degree"], reverse=True)
    return significant[:20]  # top 20


def compute_surface_stats(roads_geojson: dict) -> dict[str, float]:
    """Compute km of road by surface type."""
    surface_km: dict[str, float] = {}
    for feature in roads_geojson.get("features", []):
        surface = feature["properties"].get("surface", "unknown")
        length = feature["properties"].get("length_km", 0)
        surface_km[surface] = surface_km.get(surface, 0) + length
    return {k: round(v, 1) for k, v in sorted(surface_km.items(), key=lambda x: -x[1])}


def generate_network_report(
    roads_geojson: dict,
    G: nx.Graph,
    pinch_points: list[dict],
) -> dict:
    """Generate a complete network analysis report."""
    return {
        "network_stats": compute_network_stats(G),
        "surface_breakdown": compute_surface_stats(roads_geojson),
        "pinch_points": pinch_points,
        "feature_count": len(roads_geojson.get("features", [])),
    }
