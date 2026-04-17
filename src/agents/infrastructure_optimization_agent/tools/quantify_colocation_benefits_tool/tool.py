import json
import logging

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION

logger = logging.getLogger("corridor.agent.infra.colocation")

# Unit cost benchmarks for co-location savings calculation (USD per km)
GREENFIELD_COSTS = {
    "access_roads_per_km": 180_000,
    "land_clearing_per_km": 95_000,
    "land_acquisition_per_km": 210_000,
    "security_per_km_per_year": 12_000,
    "construction_logistics_per_km": 145_000,
}
COLOCATION_COSTS = {
    "access_roads_per_km": 22_000,
    "land_clearing_per_km": 18_000,
    "land_acquisition_per_km": 38_000,
    "security_per_km_per_year": 4_500,
    "construction_logistics_per_km": 61_000,
}
EIA_GREENFIELD = 8_500_000
EIA_SHARED = 2_800_000

# Estimated highway overlap percentage by terrain segment type
OVERLAP_ESTIMATES = {
    "coastal_plain": 0.78,
    "delta_wetland": 0.44,
    "urban": 0.62,
    "default": 0.65,
}


@tool("quantify_colocation_benefits", description=TOOL_DESCRIPTION)
def quantify_colocation_benefits_tool(runtime: ToolRuntime) -> Command:
    """Calculates CAPEX savings from co-locating with highway corridor using real data."""
    from src.adapters.pipeline_bridge import pipeline_bridge

    try:
        corridor = pipeline_bridge.get_corridor_info()
    except Exception as exc:
        logger.error("Corridor data unavailable: %s", exc)
        return Command(update={"messages": [ToolMessage(
            content=json.dumps({"error": str(exc), "message": "Co-location analysis failed."}),
            tool_call_id=runtime.tool_call_id,
        )]})

    nodes = corridor.get("nodes", [])
    total_km = corridor.get("length_km", 1080)

    # Get existing transmission lines for actual co-location assessment
    existing_lines_context = {}
    try:
        grid_data = pipeline_bridge.get_transmission_grid()
        summary = grid_data.get("summary", {})
        transmission_lines = grid_data.get("grid", {}).get("transmission_lines", [])
        existing_lines_context = {
            "total_existing_lines": summary.get("total_lines", 0),
            "total_existing_km": summary.get("total_km", 0),
            "by_voltage": summary.get("by_voltage", {}),
            "by_country": summary.get("by_country", {}),
            "lines": transmission_lines,
            "source": grid_data.get("source", ""),
        }
    except Exception as exc:
        logger.warning("Transmission grid data unavailable: %s", exc)

    # Build segments from corridor nodes
    segments = []
    for i in range(len(nodes) - 1):
        n1, n2 = nodes[i], nodes[i + 1]
        dlat = abs(n2["lat"] - n1["lat"])
        dlon = abs(n2["lon"] - n1["lon"])
        seg_km = round(((dlat ** 2 + dlon ** 2) ** 0.5) * 111, 1)

        overlap_pct = OVERLAP_ESTIMATES["default"]
        label = f"{n1['name']} → {n2['name']}"

        segments.append({
            "segment_id": f"SEG-C-{i + 1:03d}",
            "label": label,
            "length_km": seg_km,
            "highway_overlap_pct": round(overlap_pct * 100),
            "co_located_km": round(seg_km * overlap_pct, 1),
            "standalone_km": round(seg_km * (1 - overlap_pct), 1),
        })

    # Calculate savings per segment
    total_greenfield = 0
    total_colocation = 0
    segment_analyses = []

    for seg in segments:
        km = seg["length_km"]
        co_km = seg["co_located_km"]
        sa_km = seg["standalone_km"]

        greenfield = sum(v * km for k, v in GREENFIELD_COSTS.items())
        colocation = (
            sum(v * co_km for k, v in COLOCATION_COSTS.items())
            + sum(v * sa_km for k, v in GREENFIELD_COSTS.items())
        )
        saving = greenfield - colocation

        seg["greenfield_cost_usd"] = round(greenfield)
        seg["colocation_cost_usd"] = round(colocation)
        seg["saving_usd"] = round(saving)
        seg["saving_pct"] = round(saving / greenfield * 100, 1) if greenfield > 0 else 0

        total_greenfield += greenfield
        total_colocation += colocation
        segment_analyses.append(seg)

    # EIA savings
    eia_saving = EIA_GREENFIELD - EIA_SHARED
    total_saving = total_greenfield - total_colocation + eia_saving

    # Assess existing transmission line co-location potential
    transmission_colocation = {}
    if existing_lines_context.get("total_existing_km", 0) > 0:
        existing_km = existing_lines_context["total_existing_km"]
        # Existing transmission ROW can provide additional co-location benefits
        # (shared right-of-way, existing access roads, cleared corridors)
        potential_shared_km = min(existing_km, total_km) * 0.3  # Conservative 30% overlap estimate
        row_saving_per_km = (
            GREENFIELD_COSTS["land_acquisition_per_km"]
            - COLOCATION_COSTS["land_acquisition_per_km"]
        )
        additional_row_savings = round(potential_shared_km * row_saving_per_km)

        transmission_colocation = {
            "existing_transmission_km": existing_km,
            "existing_lines_count": existing_lines_context.get("total_existing_lines", 0),
            "by_voltage": existing_lines_context.get("by_voltage", {}),
            "estimated_shared_row_km": round(potential_shared_km, 1),
            "additional_row_savings_usd": additional_row_savings,
            "note": (
                "Existing transmission rights-of-way offer additional co-location "
                "savings beyond highway corridor sharing (shared land acquisition, "
                "existing access, cleared vegetation)."
            ),
        }
        total_saving += additional_row_savings

    # Build data sources
    data_sources = ["Corridor AOI geometry", "WAPP Regional Transmission Cost Database"]
    if existing_lines_context:
        data_sources.append(
            f"Transmission grid ({existing_lines_context.get('total_existing_lines', 0)} existing lines, "
            f"{existing_lines_context.get('total_existing_km', 0)} km)"
        )

    # Build enriched message
    tx_msg = ""
    if transmission_colocation:
        tx_msg = (
            f" Additional ROW savings from {transmission_colocation['estimated_shared_row_km']:.1f} km "
            f"shared with existing transmission: ${transmission_colocation['additional_row_savings_usd'] / 1e6:,.1f}M."
        )

    response = {
        "status": "Co-location Analysis Complete",
        "corridor_id": corridor.get("corridor_id", "AL_CORRIDOR_001"),
        "total_corridor_km": total_km,
        "segments_analyzed": len(segment_analyses),
        "greenfield_costs": GREENFIELD_COSTS,
        "colocation_costs": COLOCATION_COSTS,
        "segment_analysis": segment_analyses,
        "transmission_colocation": transmission_colocation if transmission_colocation else None,
        "summary": {
            "total_greenfield_usd": round(total_greenfield),
            "total_colocation_usd": round(total_colocation),
            "total_saving_usd": round(total_saving),
            "eia_saving_usd": eia_saving,
            "transmission_row_saving_usd": transmission_colocation.get("additional_row_savings_usd", 0),
            "saving_pct": round(total_saving / total_greenfield * 100, 1) if total_greenfield > 0 else 0,
        },
        "data_sources": data_sources,
        "message": (
            f"Co-location analysis completed for {len(segment_analyses)} segments. "
            f"Total greenfield cost: ${total_greenfield / 1e6:,.1f}M. "
            f"Co-location saving: ${total_saving / 1e6:,.1f}M "
            f"({round(total_saving / total_greenfield * 100, 1) if total_greenfield > 0 else 0}% of gross). "
            "Savings from shared access roads, land clearing, security, and EIA."
            f"{tx_msg}"
        ),
    }

    return Command(update={"messages": [ToolMessage(
        content=json.dumps(response), tool_call_id=runtime.tool_call_id,
    )]})
