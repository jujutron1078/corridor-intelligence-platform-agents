import json
import logging

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import CurrentDemandInput

logger = logging.getLogger("corridor.agent.opportunity.current_demand")

# Sector energy-intensity benchmarks (MW per unit) for demand estimation
# These are industry-standard engineering benchmarks.
SECTOR_BENCHMARKS = {
    "port_facility": {
        "base_mw": 20.0,
        "load_factor": 0.82,
        "reliability_class": "Critical",
        "basis": "Port operations: ~2.5 MW per crane + terminal lighting, reefer plugs, admin",
    },
    "airport": {
        "base_mw": 15.0,
        "load_factor": 0.75,
        "reliability_class": "Critical",
        "basis": "Airport operations: terminal HVAC, runway lighting, ATC, baggage handling",
    },
    "industrial_zone": {
        "base_mw": 30.0,
        "load_factor": 0.72,
        "reliability_class": "High",
        "basis": "Mixed light/heavy manufacturing zone: ~5-8 W/sqm built-up area average",
    },
    "mineral_site": {
        "base_mw": 25.0,
        "load_factor": 0.85,
        "reliability_class": "High",
        "basis": "Mining operations: processing, haulage, ventilation, dewatering",
    },
    "rail_network": {
        "base_mw": 5.0,
        "load_factor": 0.60,
        "reliability_class": "Standard",
        "basis": "Rail station/yard: signaling, switching, lighting, maintenance facilities",
    },
    "border_crossing": {
        "base_mw": 2.0,
        "load_factor": 0.65,
        "reliability_class": "Standard",
        "basis": "Border post: customs scanning, lighting, administration, cold storage",
    },
}


def _estimate_demand(det: dict) -> dict:
    """Estimate electricity demand for a single detection using sector benchmarks."""
    det_type = det.get("type", "other")
    props = det.get("properties", {})

    benchmark = SECTOR_BENCHMARKS.get(det_type, {
        "base_mw": 5.0,
        "load_factor": 0.65,
        "reliability_class": "Standard",
        "basis": "Generic facility estimate — verify with site-specific data",
    })

    # For power plants, use actual capacity from data
    if det_type == "power_plant":
        capacity = props.get("capacity_mw", 0)
        return {
            "current_mw": capacity,
            "load_factor": 0.75,
            "reliability_class": "Critical",
            "demand_basis": f"Generation asset: {capacity} MW installed capacity",
            "is_generation_asset": True,
        }

    # For mineral sites, scale by commodity type
    base_mw = benchmark["base_mw"]
    if det_type == "mineral_site":
        commodity = (props.get("commodity", "") or props.get("commod1", "")).lower()
        if "gold" in commodity:
            base_mw = 50.0
        elif "lithium" in commodity or "copper" in commodity:
            base_mw = 40.0
        elif "iron" in commodity or "bauxite" in commodity:
            base_mw = 35.0

    return {
        "current_mw": base_mw,
        "load_factor": benchmark["load_factor"],
        "reliability_class": benchmark["reliability_class"],
        "demand_basis": benchmark["basis"],
        "is_generation_asset": False,
    }


@tool("calculate_current_demand", description=TOOL_DESCRIPTION)
def calculate_current_demand_tool(
    payload: CurrentDemandInput, runtime: ToolRuntime
) -> Command:
    """
    Calculates current electricity demand for each anchor load using real
    infrastructure data and sector energy-intensity benchmarks.
    """
    from src.adapters.pipeline_bridge import pipeline_bridge

    try:
        infra = pipeline_bridge.get_infrastructure_detections()
    except Exception as exc:
        logger.error("Infrastructure data unavailable: %s", exc)
        return Command(update={"messages": [ToolMessage(
            content=json.dumps({
                "error": str(exc),
                "demand_profiles": [],
                "message": "Cannot calculate demand — infrastructure data unavailable.",
            }),
            tool_call_id=runtime.tool_call_id,
        )]})

    # Get power plant data for real capacity values
    energy_plants: list[dict] = []
    try:
        energy = pipeline_bridge.get_energy_data()
        for i, feat in enumerate(energy.get("power_plants", {}).get("features", [])):
            coords = feat.get("geometry", {}).get("coordinates", [])
            props = feat.get("properties", {})
            energy_plants.append({
                "detection_id": f"DET-PWR-{i + 1:03d}",
                "type": "power_plant",
                "name": props.get("name", "Unknown Power Plant"),
                "coordinates": coords,
                "source": "Global Power Plant Database",
                "properties": props,
            })
    except Exception as exc:
        logger.warning("Energy data unavailable: %s", exc)

    # Enrich port demand estimates with real throughput data
    port_throughput_context = {}
    try:
        ports_data = pipeline_bridge.get_port_statistics()
        for port in ports_data.get("ports", []):
            port_name = port.get("name", "")
            if port_name:
                teu = port.get("teu_throughput", 0)
                # Scale demand: ~1 MW per 50,000 TEU throughput as industry benchmark
                throughput_demand_mw = round(teu / 50000, 1) if teu else 0
                port_throughput_context[port_name.lower()] = {
                    "teu_throughput": teu,
                    "cargo_tons": port.get("cargo_tons", 0),
                    "throughput_implied_demand_mw": throughput_demand_mw,
                    "country": port.get("country", ""),
                }
        logger.info("Port throughput data obtained: %d ports", len(port_throughput_context))
    except Exception as exc:
        logger.warning("Port statistics unavailable: %s", exc)

    all_detections = infra.get("detections", []) + energy_plants

    demand_profiles = []
    generation_assets = []
    total_demand_mw = 0.0
    by_reliability: dict[str, int] = {}
    by_sector_mw: dict[str, float] = {}
    by_country_mw: dict[str, float] = {}

    for i, det in enumerate(all_detections):
        estimate = _estimate_demand(det)
        props = det.get("properties", {})
        country = props.get("country", props.get("addr:country", "Unknown"))
        det_type = det.get("type", "other")
        sector = {
            "port_facility": "Industrial",
            "airport": "Industrial",
            "industrial_zone": "Industrial",
            "mineral_site": "Mining",
            "rail_network": "Industrial",
            "border_crossing": "Industrial",
            "power_plant": "Energy",
        }.get(det_type, "Other")

        profile = {
            "anchor_id": f"AL_ANC_{i + 1:03d}",
            "detection_id": det.get("detection_id", f"DET-{i + 1:03d}"),
            "entity_name": det.get("name", "Unknown"),
            "country": country,
            "sector": sector,
            "type": det_type,
            "current_mw": estimate["current_mw"],
            "load_factor": estimate["load_factor"],
            "reliability_class": estimate["reliability_class"],
            "demand_basis": estimate["demand_basis"],
        }

        # Adjust port demand using real throughput data if available
        if det_type == "port_facility" and port_throughput_context:
            name_lower = det.get("name", "").lower()
            for port_key, port_info in port_throughput_context.items():
                if port_key in name_lower or name_lower in port_key:
                    implied_mw = port_info.get("throughput_implied_demand_mw", 0)
                    if implied_mw > 0:
                        profile["current_mw"] = max(profile["current_mw"], implied_mw)
                        profile["demand_basis"] += f" (adjusted via TEU throughput: {port_info['teu_throughput']:,} TEU)"
                        profile["port_throughput"] = port_info
                    break

        if estimate.get("is_generation_asset"):
            generation_assets.append(profile)
        else:
            demand_profiles.append(profile)
            total_demand_mw += estimate["current_mw"]
            rc = estimate["reliability_class"]
            by_reliability[rc] = by_reliability.get(rc, 0) + 1
            by_sector_mw[sector] = by_sector_mw.get(sector, 0) + estimate["current_mw"]
            by_country_mw[country] = by_country_mw.get(country, 0) + estimate["current_mw"]

    response = {
        "total_current_mw": round(total_demand_mw, 1),
        "anchor_loads_assessed": len(demand_profiles),
        "generation_assets_excluded": len(generation_assets),
        "demand_profiles": demand_profiles,
        "port_throughput_context": port_throughput_context if port_throughput_context else {},
        "summary": {
            "total_current_mw": round(total_demand_mw, 1),
            "by_reliability_class": by_reliability,
            "by_sector_mw": {k: round(v, 1) for k, v in by_sector_mw.items()},
            "by_country_mw": {k: round(v, 1) for k, v in by_country_mw.items()},
            "ports_with_throughput_adjustments": len(port_throughput_context),
        },
        "data_sources": ["OpenStreetMap", "USGS Minerals", "Global Power Plant Database"]
            + (["Port Statistics (TEU throughput)"] if port_throughput_context else []),
        "benchmarks_applied": list(SECTOR_BENCHMARKS.keys()),
        "message": (
            f"Current demand profiles calculated for {len(demand_profiles)} anchor loads. "
            f"Total aggregated current demand: {total_demand_mw:,.1f} MW. "
            f"{len(generation_assets)} generation assets excluded from demand-side analysis."
        ),
    }

    return Command(update={"messages": [ToolMessage(
        content=json.dumps(response), tool_call_id=runtime.tool_call_id,
    )]})
