import json
import logging

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import CostEstimationInput

logger = logging.getLogger("corridor.agent.infra.cost_estimates")

# Unit cost reference table (USD) — WAPP Regional Transmission Cost Database 2024
UNIT_COSTS = {
    "transmission_lines": {
        "400kv_per_km": 1_850_000,
        "330kv_per_km": 980_000,
        "161kv_per_km": 520_000,
        "33kv_underground_per_km": 1_200_000,
    },
    "substations": {
        "400kv_per_bay": 18_000_000,
        "330kv_per_bay": 11_500_000,
        "161kv_per_bay": 6_200_000,
        "33kv_substation": 3_800_000,
    },
    "ancillary": {
        "scada_per_substation": 850_000,
        "fiber_optic_per_km": 28_000,
        "border_crossing_package": 4_500_000,
        "esia_per_segment": 2_200_000,
    },
}

# Country cost adjustment factors
COUNTRY_ADJUSTMENTS = {
    "CIV": 1.00, "GHA": 1.03, "TGO": 1.05,
    "BEN": 1.05, "NGA": 1.12,
}

CONTINGENCY_PCT = 0.15
OPEX_PCT = 0.026  # 2.6% of CAPEX annually


@tool("generate_cost_estimates", description=TOOL_DESCRIPTION)
def generate_cost_estimates_tool(
    payload: CostEstimationInput, runtime: ToolRuntime
) -> Command:
    """Calculates total project CAPEX and annual OPEX using real corridor data."""
    from src.adapters.pipeline_bridge import pipeline_bridge

    try:
        corridor = pipeline_bridge.get_corridor_info()
    except Exception as exc:
        logger.error("Corridor data unavailable: %s", exc)
        return Command(update={"messages": [ToolMessage(
            content=json.dumps({"error": str(exc), "cost_summary": {},
                                "message": "Cost estimation failed — corridor data unavailable."}),
            tool_call_id=runtime.tool_call_id,
        )]})

    nodes = corridor.get("nodes", [])
    total_km = corridor.get("length_km", 1080)
    countries = corridor.get("countries", [])

    # Get existing transmission grid for potential cost offsets
    grid_context = {}
    try:
        grid_data = pipeline_bridge.get_transmission_grid()
        summary = grid_data.get("summary", {})
        existing_substations = grid_data.get("grid", {}).get("substations", [])
        grid_context = {
            "total_existing_lines": summary.get("total_lines", 0),
            "total_existing_km": summary.get("total_km", 0),
            "existing_substations": len(existing_substations),
            "by_voltage": summary.get("by_voltage", {}),
            "by_country": summary.get("by_country", {}),
            "source": grid_data.get("source", ""),
        }
    except Exception as exc:
        logger.warning("Transmission grid data unavailable: %s", exc)

    # Get WAPP data for investment sizing context
    wapp_context = {}
    try:
        wapp_data = pipeline_bridge.get_wapp_data()
        wapp_context = {
            "generation_targets": wapp_data.get("generation_targets", {}),
            "trade_volumes": wapp_data.get("trade_volumes", {}),
            "source": wapp_data.get("source", ""),
        }
    except Exception as exc:
        logger.warning("WAPP data unavailable: %s", exc)

    # Build segments and estimate costs
    segments = []
    total_line_cost = 0
    total_sub_cost = 0
    total_ancillary = 0

    for i in range(len(nodes) - 1):
        n1, n2 = nodes[i], nodes[i + 1]
        dlat = abs(n2["lat"] - n1["lat"])
        dlon = abs(n2["lon"] - n1["lon"])
        seg_km = round(((dlat ** 2 + dlon ** 2) ** 0.5) * 111, 1)

        # Default to 330kV for backbone segments
        line_cost_per_km = UNIT_COSTS["transmission_lines"]["330kv_per_km"]
        line_cost = seg_km * line_cost_per_km
        sub_cost = UNIT_COSTS["substations"]["330kv_per_bay"] * 2  # 2 bays per segment end
        ancillary = (
            UNIT_COSTS["ancillary"]["fiber_optic_per_km"] * seg_km
            + UNIT_COSTS["ancillary"]["scada_per_substation"]
            + UNIT_COSTS["ancillary"]["esia_per_segment"]
        )

        total_line_cost += line_cost
        total_sub_cost += sub_cost
        total_ancillary += ancillary

        segments.append({
            "segment_id": f"SEG-CE-{i + 1:03d}",
            "from_node": n1["name"],
            "to_node": n2["name"],
            "length_km": seg_km,
            "voltage_kv": 330,
            "line_cost_usd": round(line_cost),
            "substation_cost_usd": round(sub_cost),
            "ancillary_cost_usd": round(ancillary),
            "segment_total_usd": round(line_cost + sub_cost + ancillary),
        })

    # Border crossing costs
    border_crossings = max(len(countries) - 1, 0)
    border_cost = border_crossings * UNIT_COSTS["ancillary"]["border_crossing_package"]
    total_ancillary += border_cost

    subtotal = total_line_cost + total_sub_cost + total_ancillary
    contingency = subtotal * CONTINGENCY_PCT
    total_capex = subtotal + contingency
    annual_opex = total_capex * OPEX_PCT

    # Calculate potential cost offsets from existing infrastructure
    infrastructure_offsets = {}
    if grid_context:
        existing_sub_count = grid_context.get("existing_substations", 0)
        # Existing substations that could be upgraded instead of built new save ~40%
        potential_sub_savings = 0
        if existing_sub_count > 0:
            upgradeable = min(existing_sub_count, len(nodes))
            potential_sub_savings = round(
                upgradeable * UNIT_COSTS["substations"]["330kv_per_bay"] * 0.40
            )
        infrastructure_offsets = {
            "existing_substations_in_corridor": existing_sub_count,
            "potential_substation_upgrade_savings_usd": potential_sub_savings,
            "existing_transmission_km": grid_context.get("total_existing_km", 0),
            "note": (
                "Existing substations may be upgradeable rather than built greenfield, "
                "reducing substation costs by up to 40% per upgradeable site."
            ),
        }

    # Build data sources
    data_sources = ["Corridor AOI geometry", "WAPP cost database"]
    if grid_context:
        data_sources.append(f"Transmission grid ({grid_context.get('total_existing_lines', 0)} existing lines)")
    if wapp_context:
        data_sources.append("WAPP generation targets")

    # Build enriched message
    offset_msg = ""
    if infrastructure_offsets.get("potential_substation_upgrade_savings_usd", 0) > 0:
        savings = infrastructure_offsets["potential_substation_upgrade_savings_usd"]
        offset_msg = f" Potential savings from upgrading {infrastructure_offsets['existing_substations_in_corridor']} existing substations: ${savings / 1e6:,.1f}M."
    wapp_msg = ""
    if wapp_context.get("generation_targets"):
        wapp_msg = " WAPP generation targets contextualize investment sizing against regional capacity plans."

    response = {
        "corridor_id": corridor.get("corridor_id", "AL_CORRIDOR_001"),
        "cost_basis": {
            "pricing_date": "Q1 2026",
            "currency": "USD",
            "contingency_pct": CONTINGENCY_PCT * 100,
            "unit_cost_source": "WAPP Regional Transmission Cost Database 2024",
            "country_adjustments": COUNTRY_ADJUSTMENTS,
        },
        "unit_costs_usd": UNIT_COSTS,
        "capex_by_segment": segments,
        "cost_summary": {
            "line_costs_usd": round(total_line_cost),
            "substation_costs_usd": round(total_sub_cost),
            "ancillary_costs_usd": round(total_ancillary),
            "border_crossing_costs_usd": round(border_cost),
            "subtotal_before_contingency_usd": round(subtotal),
            "contingency_usd": round(contingency),
            "total_capex_usd": round(total_capex),
            "annual_opex_usd": round(annual_opex),
            "opex_as_pct_of_capex": OPEX_PCT * 100,
        },
        "infrastructure_offsets": infrastructure_offsets if infrastructure_offsets else None,
        "wapp_investment_context": wapp_context if wapp_context else None,
        "cost_by_category_pct": {
            "transmission_lines": round(total_line_cost / subtotal * 100, 1) if subtotal > 0 else 0,
            "substations": round(total_sub_cost / subtotal * 100, 1) if subtotal > 0 else 0,
            "ancillary": round(total_ancillary / subtotal * 100, 1) if subtotal > 0 else 0,
        },
        "data_sources": data_sources,
        "message": (
            f"Cost estimates generated for {len(segments)} segments across {total_km} km. "
            f"Total CAPEX (incl. {CONTINGENCY_PCT * 100}% contingency): "
            f"${total_capex / 1e6:,.1f}M. "
            f"Annual OPEX: ${annual_opex / 1e6:,.1f}M ({OPEX_PCT * 100}% of CAPEX). "
            f"{border_crossings} border crossings at ${UNIT_COSTS['ancillary']['border_crossing_package'] / 1e6:.1f}M each."
            f"{offset_msg}{wapp_msg}"
        ),
    }

    return Command(update={"messages": [ToolMessage(
        content=json.dumps(response), tool_call_id=runtime.tool_call_id,
    )]})
