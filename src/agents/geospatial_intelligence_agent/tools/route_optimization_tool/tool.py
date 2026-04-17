import json
import logging
import math

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import RouteOptimizationInput

logger = logging.getLogger("corridor.agent.geospatial.route_optimization")

# Priority-based edge weight functions
# Tier-based cost multiplier (tier 1 = highway, tier 4 = track)
TIER_COST_MULTIPLIER = {1: 1.0, 2: 1.5, 3: 2.5, 4: 4.0}
TIER_SPEED_KMH = {1: 100, 2: 70, 3: 40, 4: 20}

# Impact scoring by proximity to infrastructure
IMPACT_BONUS = {
    "port_facility": 0.3,
    "airport": 0.2,
    "industrial_zone": 0.25,
    "mineral_site": 0.2,
    "rail_network": 0.15,
    "border_crossing": 0.1,
}


def _haversine(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Haversine distance in km."""
    R = 6371.0
    rlat1, rlat2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _find_nearest_graph_node(G, lon: float, lat: float, max_dist_km: float = 100) -> tuple | None:
    """Find the nearest graph node to a given (lon, lat) within max_dist_km."""
    best_node = None
    best_dist = max_dist_km
    for node in G.nodes():
        d = _haversine(lon, lat, node[0], node[1])
        if d < best_dist:
            best_dist = d
            best_node = node
    return best_node


def _compute_edge_weight(edge_data: dict, priority: str) -> float:
    """Compute edge weight based on optimization priority."""
    length = edge_data.get("length_km", 1.0)
    tier = edge_data.get("tier", 4)

    if priority == "min_distance":
        return length
    elif priority == "min_cost":
        # Cost proportional to distance × construction difficulty
        return length * TIER_COST_MULTIPLIER.get(tier, 4.0)
    elif priority == "max_impact":
        # Favor higher-tier roads (better connected = more impact)
        # Lower weight = preferred, so invert tier benefit
        impact_factor = 1.0 / (tier + 0.5)
        return length * (1.0 - impact_factor * 0.5)
    else:  # balance
        cost_factor = TIER_COST_MULTIPLIER.get(tier, 4.0)
        return length * (0.5 + 0.5 * cost_factor / 4.0)


@tool("route_optimization", description=TOOL_DESCRIPTION)
def route_optimization_tool(
    payload: RouteOptimizationInput, runtime: ToolRuntime
) -> Command:
    """
    Calculates optimized route variants using real road network data from OSM
    with NetworkX graph-based shortest path algorithms.
    """
    from src.adapters.pipeline_bridge import pipeline_bridge

    corridor = None
    try:
        corridor = pipeline_bridge.get_corridor_info()
    except Exception as exc:
        logger.warning("Corridor info unavailable: %s", exc)

    nodes = corridor.get("nodes", []) if corridor else []
    countries = corridor.get("countries", []) if corridor else ["NGA", "BEN", "TGO", "GHA", "CIV"]

    # Try to build a real graph-based route
    graph_route = None
    network_stats = None
    pinch_points = []

    try:
        G = pipeline_bridge.get_road_network_graph()
        if G is not None and G.number_of_nodes() > 0:
            import networkx as nx

            logger.info("Graph loaded: %d nodes, %d edges", G.number_of_nodes(), G.number_of_edges())

            # Set edge weights based on priority
            for u, v, data in G.edges(data=True):
                data["weight"] = _compute_edge_weight(data, payload.priority)

            # Find shortest path between corridor endpoints (Lagos → Abidjan)
            start_node = _find_nearest_graph_node(G, nodes[0]["lon"], nodes[0]["lat"]) if nodes else None
            end_node = _find_nearest_graph_node(G, nodes[-1]["lon"], nodes[-1]["lat"]) if nodes else None

            if start_node and end_node:
                try:
                    path = nx.shortest_path(G, start_node, end_node, weight="weight")
                    path_edges = list(zip(path[:-1], path[1:]))

                    total_km = sum(G[u][v].get("length_km", 0) for u, v in path_edges)
                    total_weight = sum(G[u][v].get("weight", 0) for u, v in path_edges)

                    # Road quality breakdown along path
                    tier_km = {1: 0, 2: 0, 3: 0, 4: 0}
                    surface_km = {}
                    for u, v in path_edges:
                        edge = G[u][v]
                        t = edge.get("tier", 4)
                        tier_km[t] = tier_km.get(t, 0) + edge.get("length_km", 0)
                        s = edge.get("surface", "unknown")
                        surface_km[s] = surface_km.get(s, 0) + edge.get("length_km", 0)

                    # Estimated travel time
                    travel_hours = sum(
                        G[u][v].get("length_km", 0) / TIER_SPEED_KMH.get(G[u][v].get("tier", 4), 20)
                        for u, v in path_edges
                    )

                    # Sample waypoints along path (every ~50 nodes for visualization)
                    step = max(1, len(path) // 20)
                    waypoints = [{"lon": path[i][0], "lat": path[i][1]} for i in range(0, len(path), step)]

                    graph_route = {
                        "total_distance_km": round(total_km, 1),
                        "total_weighted_cost": round(total_weight, 1),
                        "estimated_travel_hours": round(travel_hours, 1),
                        "road_segments": len(path_edges),
                        "tier_breakdown_km": {f"tier_{k}": round(v, 1) for k, v in tier_km.items()},
                        "surface_breakdown_km": {k: round(v, 1) for k, v in sorted(surface_km.items(), key=lambda x: -x[1])},
                        "waypoints": waypoints,
                        "start": {"lon": start_node[0], "lat": start_node[1]},
                        "end": {"lon": end_node[0], "lat": end_node[1]},
                    }

                    logger.info("Route found: %.1f km, %.1f hours", total_km, travel_hours)

                except nx.NetworkXNoPath:
                    logger.warning("No path found between %s and %s", start_node, end_node)
                except nx.NodeNotFound as exc:
                    logger.warning("Node not found in graph: %s", exc)

            # Compute intermediate segment distances (between consecutive corridor nodes)
            segments = []
            for i in range(len(nodes) - 1):
                src = _find_nearest_graph_node(G, nodes[i]["lon"], nodes[i]["lat"])
                dst = _find_nearest_graph_node(G, nodes[i + 1]["lon"], nodes[i + 1]["lat"])
                if src and dst:
                    try:
                        seg_path = nx.shortest_path(G, src, dst, weight="weight")
                        seg_edges = list(zip(seg_path[:-1], seg_path[1:]))
                        seg_km = sum(G[u][v].get("length_km", 0) for u, v in seg_edges)
                        segments.append({
                            "from": nodes[i]["name"],
                            "to": nodes[i + 1]["name"],
                            "distance_km": round(seg_km, 1),
                            "road_segments": len(seg_edges),
                        })
                    except (nx.NetworkXNoPath, nx.NodeNotFound):
                        # Fallback to straight-line
                        straight = _haversine(nodes[i]["lon"], nodes[i]["lat"], nodes[i + 1]["lon"], nodes[i + 1]["lat"])
                        segments.append({
                            "from": nodes[i]["name"],
                            "to": nodes[i + 1]["name"],
                            "distance_km": round(straight * 1.3, 1),  # road factor
                            "road_segments": 0,
                            "note": "straight-line estimate (no graph path)",
                        })

            # Get network-wide stats
            from src.pipelines.osm_pipeline.processor import compute_network_stats, find_pinch_points
            network_stats = compute_network_stats(G)
            pinch_points = find_pinch_points(G)

    except Exception as exc:
        logger.warning("Graph-based routing failed: %s - falling back to corridor nodes", exc)

    # Build response
    response = {
        "job_metadata": {
            "corridor_id": "AL_CORRIDOR_001",
            "priority_mode": payload.priority,
            "data_sources": ["OpenStreetMap road network", "NetworkX graph routing", "SRTM elevation", "WDPA constraints"],
            "corridor_nodes": len(nodes),
            "routing_engine": "networkx" if graph_route else "corridor_geometry",
        },
        "corridor_nodes": nodes,
    }

    if graph_route:
        # Format as route_variants array for frontend map compatibility
        response["route_variants"] = [{
            "variant_id": f"OPT-{payload.priority.upper()}",
            "label": f"Optimized ({payload.priority.replace('_', ' ')})",
            "rank": 1,
            "is_recommended": True,
            "coordinates": graph_route["waypoints"],
            "distance_km": graph_route["total_distance_km"],
            "estimated_duration_hours": graph_route["estimated_travel_hours"],
            "road_segments": graph_route["road_segments"],
            "tier_breakdown_km": graph_route["tier_breakdown_km"],
            "surface_breakdown_km": graph_route["surface_breakdown_km"],
        }]
        response["optimized_route"] = graph_route
        if segments:
            response["segment_analysis"] = segments
    else:
        # Fallback: straight-line corridor analysis
        total_km = corridor.get("length_km", 1080) if corridor else 1080
        response["route_analysis"] = {
            "total_corridor_length_km": total_km,
            "countries_traversed": countries,
            "priority_mode": payload.priority,
            "note": "Graph-based routing unavailable. Run 'corridor setup' to pull OSM road data.",
        }

    if network_stats:
        response["network_stats"] = network_stats

    if pinch_points:
        response["pinch_points"] = pinch_points[:10]

    # Add existing transmission grid overlay for co-location scoring
    try:
        grid_data = pipeline_bridge.get_transmission_grid()
        grid_info = grid_data.get("grid", {})
        transmission_lines = grid_info.get("transmission_lines", [])
        substations = grid_info.get("substations", [])
        response["existing_grid_overlay"] = {
            "transmission_lines_count": len(transmission_lines),
            "substations_count": len(substations),
            "transmission_lines": transmission_lines[:20],  # Cap for response size
            "substations": substations[:20],
            "summary": grid_data.get("summary", {}),
            "source": grid_data.get("source", "Transmission Grid Database"),
            "note": "Existing grid lines can be used for co-location to reduce construction costs",
        }
        response["job_metadata"]["data_sources"].append("Transmission Grid DB")
        logger.info("Grid overlay added: %d lines, %d substations", len(transmission_lines), len(substations))
    except Exception as exc:
        logger.warning("Transmission grid data unavailable for overlay: %s", exc)

    # Add infrastructure along route
    try:
        road_data = pipeline_bridge.get_infrastructure_detections()
        if road_data and road_data.get("detections"):
            by_type = {}
            for det in road_data["detections"]:
                t = det.get("type", "other")
                by_type.setdefault(t, []).append({
                    "name": det.get("name", "Unknown"),
                    "coordinates": det.get("coordinates"),
                })
            response["infrastructure_along_route"] = {
                dtype: {"count": len(items), "items": items[:10]}
                for dtype, items in by_type.items()
            }
    except Exception as exc:
        logger.warning("Infrastructure data unavailable: %s", exc)

    response["message"] = (
        f"Route optimization ({payload.priority}): "
        + (
            f"{graph_route['total_distance_km']} km via {graph_route['road_segments']} road segments, "
            f"est. {graph_route['estimated_travel_hours']} hours. "
            f"Road quality: {graph_route['tier_breakdown_km']}."
            if graph_route
            else f"Corridor length ~{corridor.get('length_km', 1080) if corridor else 1080} km across {len(countries)} countries."
        )
    )

    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=json.dumps(response), tool_call_id=runtime.tool_call_id
                )
            ]
        }
    )
