import json
import logging

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import SubstationPlacementInput
from src.shared.agents.utils.coords import extract_lon_lat

logger = logging.getLogger("corridor.agent.infra.substation_placement")

# Demand benchmarks by detection type (MW)
DEMAND_BY_TYPE = {
    "port_facility": 20.0, "airport": 15.0, "industrial_zone": 30.0,
    "mineral_site": 25.0, "rail_network": 5.0, "border_crossing": 2.0,
}


@tool("optimize_substation_placement", description=TOOL_DESCRIPTION)
def optimize_substation_placement_tool(
    payload: SubstationPlacementInput, runtime: ToolRuntime
) -> Command:
    """Determines optimal substation locations based on real infrastructure data."""
    from src.adapters.pipeline_bridge import pipeline_bridge

    try:
        corridor = pipeline_bridge.get_corridor_info()
    except Exception as exc:
        logger.error("Corridor data unavailable: %s", exc)
        return Command(update={"messages": [ToolMessage(
            content=json.dumps({"error": str(exc), "hubs": [],
                                "message": "Substation placement failed — corridor data unavailable."}),
            tool_call_id=runtime.tool_call_id,
        )]})

    nodes = corridor.get("nodes", [])

    # Get infrastructure locations for load proximity analysis
    demand_points: list[dict] = []
    try:
        infra = pipeline_bridge.get_infrastructure_detections()
        for det in infra.get("detections", []):
            dt = det.get("type", "other")
            if dt == "power_plant":
                continue
            coords = det.get("coordinates", [])
            pt = extract_lon_lat(coords)
            if pt:
                demand_points.append({
                    "name": det.get("name", "Unknown"),
                    "type": dt,
                    "lon": pt[0],
                    "lat": pt[1],
                    "demand_mw": DEMAND_BY_TYPE.get(dt, 5.0),
                })
    except Exception as exc:
        logger.warning("Infrastructure data unavailable: %s", exc)

    # Get existing substations to avoid duplication
    existing_substations: list[dict] = []
    grid_summary = {}
    try:
        grid_data = pipeline_bridge.get_transmission_grid()
        grid_summary = grid_data.get("summary", {})
        existing_substations = grid_data.get("grid", {}).get("substations", [])
    except Exception as exc:
        logger.warning("Transmission grid data unavailable: %s", exc)

    # Get planned energy projects for generation co-location opportunities
    planned_projects_context = {}
    try:
        planned = pipeline_bridge.get_planned_energy_projects()
        planned_projects_context = {
            "project_count": planned.get("project_count", 0),
            "capacity_summary": planned.get("capacity_summary", {}),
            "projects": planned.get("projects", []),
            "source": planned.get("source", ""),
        }
    except Exception as exc:
        logger.warning("Planned energy projects data unavailable: %s", exc)

    # Place primary hubs at corridor nodes (cities)
    # In production, this would use K-means clustering on demand points
    primary_hubs = []
    for node in nodes:
        # Count nearby demand points (within ~0.5 degrees ≈ 55km)
        nearby = [
            dp for dp in demand_points
            if abs(dp["lat"] - node["lat"]) < 0.5
            and abs(dp["lon"] - node["lon"]) < 0.5
        ]
        nearby_mw = sum(dp["demand_mw"] for dp in nearby)

        if nearby_mw > 0:
            # Determine voltage based on demand
            if nearby_mw >= 400:
                voltage = "400kV"
            elif nearby_mw >= 100:
                voltage = "330kV"
            elif nearby_mw >= 20:
                voltage = "161kV"
            else:
                voltage = "33kV"

            # Check for existing substations nearby (within ~0.3 degrees ≈ 33km)
            nearby_existing = []
            for es in existing_substations:
                es_coords = es.get("coordinates", es.get("coords", []))
                es_pt = extract_lon_lat(es_coords)
                if es_pt:
                    es_lon, es_lat = es_pt
                    if (abs(es_lat - node["lat"]) < 0.3
                            and abs(es_lon - node["lon"]) < 0.3):
                        nearby_existing.append({
                            "name": es.get("name", "Existing substation"),
                            "voltage": es.get("voltage", "unknown"),
                        })

            hub_entry = {
                "hub_id": f"HUB_{node['name'].upper().replace(' ', '_')[:20]}",
                "name": f"{node['name']} {voltage} Hub",
                "coords": [node["lat"], node["lon"]],
                "country": node.get("country", ""),
                "voltage_level": voltage,
                "capacity_mw": round(nearby_mw * 1.3, 1),  # 30% headroom
                "anchor_loads_nearby": len(nearby),
                "nearby_demand_mw": round(nearby_mw, 1),
                "anchors_served": [dp["name"] for dp in nearby[:5]],
            }

            if nearby_existing:
                hub_entry["existing_substations_nearby"] = nearby_existing
                hub_entry["recommendation"] = (
                    "Upgrade/expand existing substation rather than greenfield build"
                    if len(nearby_existing) > 0 else "New build recommended"
                )

            primary_hubs.append(hub_entry)

    # Count hubs with existing substations nearby
    hubs_with_existing = sum(1 for h in primary_hubs if h.get("existing_substations_nearby"))

    # Build data sources
    data_sources = ["Corridor AOI nodes", "OSM + USGS infrastructure detections"]
    if existing_substations:
        data_sources.append(f"Transmission grid ({len(existing_substations)} existing substations)")
    if planned_projects_context.get("project_count", 0) > 0:
        data_sources.append(f"Planned energy projects ({planned_projects_context['project_count']} projects)")

    # Build enriched message
    existing_msg = ""
    if hubs_with_existing > 0:
        existing_msg = (
            f" {hubs_with_existing} proposed hubs near existing substations "
            "(upgrade recommended over greenfield)."
        )
    planned_msg = ""
    if planned_projects_context.get("project_count", 0) > 0:
        planned_msg = (
            f" {planned_projects_context['project_count']} planned energy projects "
            "identified for generation co-location opportunities."
        )

    response = {
        "corridor_id": corridor.get("corridor_id", "AL_CORRIDOR_001"),
        "placement_philosophy": (
            "Substations placed at corridor nodes (major cities) nearest to "
            "detected anchor load clusters. Voltage level and capacity sized "
            "based on aggregate demand within 55km radius. 30% capacity headroom "
            "applied for growth. Existing substations checked to avoid duplication."
        ),
        "primary_hubs": primary_hubs,
        "total_hubs": len(primary_hubs),
        "hubs_near_existing_substations": hubs_with_existing,
        "total_demand_points_analyzed": len(demand_points),
        "existing_substations_in_corridor": len(existing_substations),
        "planned_energy_projects": planned_projects_context if planned_projects_context else None,
        "corridor_summary": {
            "total_hubs": len(primary_hubs),
            "total_capacity_mw": round(sum(h["capacity_mw"] for h in primary_hubs), 1),
            "by_voltage": {},
        },
        "data_sources": data_sources,
        "message": (
            f"{len(primary_hubs)} substation hubs placed along corridor at major nodes. "
            f"{len(demand_points)} demand points analyzed for proximity clustering. "
            "Hub voltage and capacity sized based on nearby anchor load demand."
            f"{existing_msg}{planned_msg}"
        ),
    }

    # Voltage distribution
    for hub in primary_hubs:
        v = hub["voltage_level"]
        response["corridor_summary"]["by_voltage"][v] = (
            response["corridor_summary"]["by_voltage"].get(v, 0) + 1
        )

    return Command(update={"messages": [ToolMessage(
        content=json.dumps(response), tool_call_id=runtime.tool_call_id,
    )]})
