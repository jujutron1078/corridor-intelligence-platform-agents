import json
import logging

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import PhasingInput

logger = logging.getLogger("corridor.agent.infra.phasing")

# Demand benchmarks by detection type (MW)
DEMAND_BY_TYPE = {
    "port_facility": 20.0, "airport": 15.0, "industrial_zone": 30.0,
    "mineral_site": 25.0, "rail_network": 5.0, "border_crossing": 2.0,
}

# Phase assignment thresholds
PHASE_1_DEMAND_MW = 20.0  # Critical anchors ≥20 MW
PHASE_2_DEMAND_MW = 10.0  # Medium anchors ≥10 MW
# Phase 3: everything else


@tool("generate_phasing_strategy", description=TOOL_DESCRIPTION)
def generate_phasing_strategy_tool(
    payload: PhasingInput, runtime: ToolRuntime
) -> Command:
    """Generates multi-phase construction plan using real infrastructure data."""
    from src.adapters.pipeline_bridge import pipeline_bridge

    try:
        corridor = pipeline_bridge.get_corridor_info()
    except Exception as exc:
        logger.error("Corridor data unavailable: %s", exc)
        return Command(update={"messages": [ToolMessage(
            content=json.dumps({"error": str(exc), "phasing_plan": [],
                                "message": "Phasing strategy failed — corridor data unavailable."}),
            tool_call_id=runtime.tool_call_id,
        )]})

    nodes = corridor.get("nodes", [])

    # Get infrastructure for demand-based phasing
    detections: list[dict] = []
    try:
        infra = pipeline_bridge.get_infrastructure_detections()
        detections = infra.get("detections", [])
    except Exception as exc:
        logger.warning("Infrastructure data unavailable: %s", exc)

    # Get WAPP interconnection data for timeline alignment
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

    # Get planned energy projects for generation capacity alignment
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

    # Classify anchors into phases by demand
    phase_1_anchors = []
    phase_2_anchors = []
    phase_3_anchors = []

    for det in detections:
        dt = det.get("type", "other")
        if dt == "power_plant":
            continue
        mw = DEMAND_BY_TYPE.get(dt, 5.0)
        entry = {
            "detection_id": det.get("detection_id", ""),
            "name": det.get("name", "Unknown"),
            "type": dt,
            "demand_mw": mw,
        }
        if mw >= PHASE_1_DEMAND_MW:
            phase_1_anchors.append(entry)
        elif mw >= PHASE_2_DEMAND_MW:
            phase_2_anchors.append(entry)
        else:
            phase_3_anchors.append(entry)

    phase_1_mw = sum(a["demand_mw"] for a in phase_1_anchors)
    phase_2_mw = sum(a["demand_mw"] for a in phase_2_anchors)
    phase_3_mw = sum(a["demand_mw"] for a in phase_3_anchors)

    phasing_plan = [
        {
            "phase": 1,
            "name": "Critical Anchor Connectivity",
            "years": "1-3",
            "description": "Connect highest-demand anchor loads to establish revenue base.",
            "anchor_count": len(phase_1_anchors),
            "total_demand_mw": round(phase_1_mw, 1),
            "anchors": phase_1_anchors,
            "priority": "Critical-class anchors (ports, industrial zones, mines ≥20 MW)",
        },
        {
            "phase": 2,
            "name": "Coastal Backbone Completion",
            "years": "3-6",
            "description": "Complete backbone and connect medium-demand facilities.",
            "anchor_count": len(phase_2_anchors),
            "total_demand_mw": round(phase_2_mw, 1),
            "anchors": phase_2_anchors,
            "priority": "Medium-demand anchors (airports, smaller zones ≥10 MW)",
        },
        {
            "phase": 3,
            "name": "Optimisation and Extensions",
            "years": "6-8",
            "description": "Connect remaining facilities and distribution reinforcements.",
            "anchor_count": len(phase_3_anchors),
            "total_demand_mw": round(phase_3_mw, 1),
            "anchors": phase_3_anchors,
            "priority": "Smaller facilities and catalytic connections",
        },
    ]

    total_mw = phase_1_mw + phase_2_mw + phase_3_mw
    total_anchors = len(phase_1_anchors) + len(phase_2_anchors) + len(phase_3_anchors)

    # Build data sources
    data_sources = ["Corridor AOI", "OSM + USGS infrastructure"]
    if wapp_context:
        data_sources.append("WAPP interconnection timeline")
    if planned_projects_context:
        data_sources.append(f"Planned energy projects ({planned_projects_context.get('project_count', 0)} projects)")

    # Build enriched message parts
    wapp_msg = ""
    if wapp_context.get("interconnections"):
        wapp_msg = f" Phasing aligned with {len(wapp_context['interconnections'])} WAPP interconnection corridors."
    planned_msg = ""
    if planned_projects_context.get("project_count", 0) > 0:
        cap = planned_projects_context.get("capacity_summary", {})
        total_planned_mw = cap.get("total_mw", 0) if isinstance(cap, dict) else 0
        planned_msg = (
            f" {planned_projects_context['project_count']} planned energy projects "
            f"({total_planned_mw:,.0f} MW) inform generation co-location timing."
        )

    response = {
        "corridor_id": corridor.get("corridor_id", "AL_CORRIDOR_001"),
        "phasing_philosophy": (
            "Construction sequenced to maximize early revenue by prioritizing "
            "segments with highest anchor load density and most creditworthy off-takers. "
            "Each phase aligned with corridor highway construction lots where possible."
        ),
        "phasing_plan": phasing_plan,
        "wapp_interconnection_context": wapp_context if wapp_context else None,
        "planned_energy_projects": planned_projects_context if planned_projects_context else None,
        "corridor_summary": {
            "total_phases": 3,
            "total_construction_years": 8,
            "total_anchors_phased": total_anchors,
            "total_demand_mw": round(total_mw, 1),
            "phase_1_mw": round(phase_1_mw, 1),
            "phase_2_mw": round(phase_2_mw, 1),
            "phase_3_mw": round(phase_3_mw, 1),
        },
        "data_sources": data_sources,
        "message": (
            f"3-Phase strategy generated for {total_anchors} anchor loads "
            f"({total_mw:,.1f} MW total). "
            f"Phase 1: {len(phase_1_anchors)} critical anchors ({phase_1_mw:,.1f} MW). "
            f"Phase 2: {len(phase_2_anchors)} medium anchors ({phase_2_mw:,.1f} MW). "
            f"Phase 3: {len(phase_3_anchors)} extensions ({phase_3_mw:,.1f} MW)."
            f"{wapp_msg}{planned_msg}"
        ),
    }

    return Command(update={"messages": [ToolMessage(
        content=json.dumps(response), tool_call_id=runtime.tool_call_id,
    )]})
