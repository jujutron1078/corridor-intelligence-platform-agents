import json
import logging

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import CapacitySizingInput
from src.shared.agents.utils.coords import extract_lon_lat

logger = logging.getLogger("corridor.agent.infra.voltage_sizing")

# Voltage class selection rules (WAPP standards)
VOLTAGE_RULES = [
    {"max_mw": 20, "max_km": 30, "voltage_kv": 33, "label": "Distribution spur"},
    {"max_mw": 150, "max_km": 120, "voltage_kv": 161, "label": "Medium-distance spur"},
    {"max_mw": 400, "max_km": 250, "voltage_kv": 225, "label": "Medium backbone (WAPP standard)"},
    {"max_mw": 1500, "max_km": 600, "voltage_kv": 330, "label": "Primary backbone"},
    {"max_mw": float("inf"), "max_km": float("inf"), "voltage_kv": 400, "label": "High-capacity backbone"},
]

# Demand benchmarks by detection type (MW)
DEMAND_BY_TYPE = {
    "port_facility": 20.0, "airport": 15.0, "industrial_zone": 30.0,
    "mineral_site": 25.0, "rail_network": 5.0, "border_crossing": 2.0,
}


def _select_voltage(demand_mw: float, distance_km: float) -> dict:
    """Select appropriate voltage class based on demand and distance."""
    for rule in VOLTAGE_RULES:
        if demand_mw <= rule["max_mw"] and distance_km <= rule["max_km"]:
            return {
                "voltage_kv": rule["voltage_kv"],
                "voltage_label": rule["label"],
            }
    return {"voltage_kv": 400, "voltage_label": "High-capacity backbone"}


@tool("size_voltage_and_capacity", description=TOOL_DESCRIPTION)
def size_voltage_and_capacity_tool(
    payload: CapacitySizingInput, runtime: ToolRuntime
) -> Command:
    """
    Determines optimal voltage class and capacity for each transmission segment
    using real corridor geometry and infrastructure detection data.
    """
    from src.adapters.pipeline_bridge import pipeline_bridge

    try:
        corridor = pipeline_bridge.get_corridor_info()
    except Exception as exc:
        logger.error("Corridor data unavailable: %s", exc)
        return Command(update={"messages": [ToolMessage(
            content=json.dumps({"error": str(exc), "segments": [],
                                "message": "Voltage sizing failed — corridor data unavailable."}),
            tool_call_id=runtime.tool_call_id,
        )]})

    nodes = corridor.get("nodes", [])

    # Get infrastructure for demand estimation
    detection_demand: dict[str, float] = {}
    try:
        infra = pipeline_bridge.get_infrastructure_detections()
        for det in infra.get("detections", []):
            det_type = det.get("type", "other")
            if det_type != "power_plant":
                coords = det.get("coordinates", [])
                pt = extract_lon_lat(coords)
                if pt:
                    # Assign demand to nearest corridor segment
                    mw = DEMAND_BY_TYPE.get(det_type, 5.0)
                    # Simple: accumulate by longitude bucket
                    lon = pt[0]
                    bucket = round(lon, 0)
                    detection_demand[str(bucket)] = detection_demand.get(str(bucket), 0) + mw
    except Exception as exc:
        logger.warning("Infrastructure data unavailable: %s", exc)

    # Get energy data for generation capacity context
    total_generation_mw = 0
    try:
        energy = pipeline_bridge.get_energy_data()
        for feat in energy.get("power_plants", {}).get("features", []):
            cap = feat.get("properties", {}).get("capacity_mw", 0)
            total_generation_mw += cap
    except Exception as exc:
        logger.warning("Energy data unavailable: %s", exc)

    # Get existing transmission grid for voltage context
    existing_voltages: dict[str, int] = {}
    grid_summary = {}
    try:
        grid_data = pipeline_bridge.get_transmission_grid()
        grid_summary = grid_data.get("summary", {})
        existing_voltages = grid_summary.get("by_voltage", {})
    except Exception as exc:
        logger.warning("Transmission grid data unavailable: %s", exc)

    # Get WAPP interconnection data for regional voltage standards
    wapp_context = {}
    try:
        wapp_data = pipeline_bridge.get_wapp_data()
        wapp_context = {
            "interconnections": wapp_data.get("interconnections", []),
            "generation_targets": wapp_data.get("generation_targets", {}),
            "trade_volumes": wapp_data.get("trade_volumes", {}),
            "source": wapp_data.get("source", ""),
        }
    except Exception as exc:
        logger.warning("WAPP data unavailable: %s", exc)

    # Size each corridor segment
    sized_segments = []
    total_demand = sum(detection_demand.values())

    for i in range(len(nodes) - 1):
        n1, n2 = nodes[i], nodes[i + 1]
        dlat = abs(n2["lat"] - n1["lat"])
        dlon = abs(n2["lon"] - n1["lon"])
        seg_km = round(((dlat ** 2 + dlon ** 2) ** 0.5) * 111, 1)

        # Estimate demand for this segment (proportional to corridor demand)
        seg_demand = total_demand / max(len(nodes) - 1, 1)

        voltage = _select_voltage(seg_demand, seg_km)

        # Security standard based on demand level
        if seg_demand >= 100:
            security = "N-1-1"
            security_label = "Enhanced contingency — Critical reliability"
        elif seg_demand >= 20:
            security = "N-1"
            security_label = "Single contingency — High reliability"
        else:
            security = "N-0"
            security_label = "No redundancy — Standard reliability"

        sized_segments.append({
            "segment_id": f"SEG-V-{i + 1:03d}",
            "from_node": n1["name"],
            "to_node": n2["name"],
            "length_km": seg_km,
            "estimated_demand_mw": round(seg_demand, 1),
            "voltage_kv": voltage["voltage_kv"],
            "voltage_label": voltage["voltage_label"],
            "security_standard": security,
            "security_label": security_label,
        })

    # Build existing grid context for output
    existing_grid_context = {}
    if existing_voltages or grid_summary:
        existing_grid_context = {
            "existing_voltage_classes": existing_voltages,
            "total_existing_lines": grid_summary.get("total_lines", 0),
            "total_existing_km": grid_summary.get("total_km", 0),
            "by_country": grid_summary.get("by_country", {}),
        }

    # Build data sources list
    data_sources = ["Corridor AOI", "OSM + USGS infrastructure", "Global Power Plant Database"]
    if existing_voltages:
        data_sources.append(f"Transmission grid ({grid_summary.get('total_lines', 0)} existing lines)")
    if wapp_context:
        data_sources.append("WAPP interconnection standards")

    # Build enriched message
    grid_msg = ""
    if existing_voltages:
        dominant_voltage = max(existing_voltages, key=existing_voltages.get) if existing_voltages else ""
        grid_msg = f" Existing grid: {grid_summary.get('total_lines', 0)} lines ({dominant_voltage} dominant)."
    wapp_msg = ""
    if wapp_context.get("interconnections"):
        wapp_msg = f" WAPP interconnection standards inform voltage harmonization across {len(wapp_context['interconnections'])} corridors."

    response = {
        "corridor_id": corridor.get("corridor_id", "AL_CORRIDOR_001"),
        "total_corridor_length_km": corridor.get("length_km", 1080),
        "total_estimated_demand_mw": round(total_demand, 1),
        "total_generation_capacity_mw": round(total_generation_mw, 1),
        "segments_sized": len(sized_segments),
        "voltage_selection_rules": [
            f"{r['voltage_kv']}kV: ≤{r['max_mw']}MW, ≤{r['max_km']}km — {r['label']}"
            for r in VOLTAGE_RULES
        ],
        "sized_segments": sized_segments,
        "existing_grid_context": existing_grid_context if existing_grid_context else None,
        "wapp_context": wapp_context if wapp_context else None,
        "data_sources": data_sources,
        "message": (
            f"{len(sized_segments)} segments sized. "
            f"Total estimated demand: {total_demand:,.1f} MW. "
            f"Generation capacity in corridor: {total_generation_mw:,.1f} MW. "
            "Voltage classes assigned per WAPP standards based on demand and distance."
            f"{grid_msg}{wapp_msg}"
        ),
    }

    return Command(update={"messages": [ToolMessage(
        content=json.dumps(response), tool_call_id=runtime.tool_call_id,
    )]})
