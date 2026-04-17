import json
import logging

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import GrowthTrajectoryInput

logger = logging.getLogger("corridor.agent.opportunity.growth_trajectory")

# Default annual growth rates by sector (used when World Bank data unavailable)
SECTOR_GROWTH_RATES = {
    "Industrial": 0.06,   # 6% p.a. — ports, SEZs, manufacturing
    "Mining": 0.04,       # 4% p.a. — mineral extraction
    "Energy": 0.03,       # 3% p.a. — refinery/processing
    "Digital": 0.12,      # 12% p.a. — data centers, telecoms
    "Agriculture": 0.05,  # 5% p.a. — agro-processing
    "Other": 0.04,
}

# Corridor countries
CORRIDOR_COUNTRIES = ["NGA", "GHA", "CIV", "TGO", "BEN"]


def _project_demand(current_mw: float, growth_rate: float, years: int) -> float:
    """Simple compound growth projection."""
    return round(current_mw * (1 + growth_rate) ** years, 1)


@tool("model_growth_trajectory", description=TOOL_DESCRIPTION)
def model_growth_trajectory_tool(
    payload: GrowthTrajectoryInput, runtime: ToolRuntime
) -> Command:
    """
    Projects 20-year electricity demand trajectories using real World Bank
    economic indicators and sector growth models.
    """
    from src.adapters.pipeline_bridge import pipeline_bridge

    # Get World Bank indicators for GDP growth context
    wb_indicators = None
    try:
        wb_data = pipeline_bridge.get_worldbank_indicators()
        wb_indicators = wb_data.get("indicators", {})
        logger.info("World Bank indicators obtained for growth modeling")
    except Exception as exc:
        logger.warning("World Bank data unavailable, using sector defaults: %s", exc)

    # Get infrastructure detections for facility-level projections
    try:
        infra = pipeline_bridge.get_infrastructure_detections()
    except Exception as exc:
        logger.error("Infrastructure data unavailable: %s", exc)
        return Command(update={"messages": [ToolMessage(
            content=json.dumps({
                "error": str(exc),
                "trajectories": [],
                "message": "Cannot model growth — infrastructure data unavailable.",
            }),
            tool_call_id=runtime.tool_call_id,
        )]})

    # Get energy data for power plant capacities
    energy_plants: list[dict] = []
    try:
        energy = pipeline_bridge.get_energy_data()
        for feat in energy.get("power_plants", {}).get("features", []):
            props = feat.get("properties", {})
            energy_plants.append({
                "type": "power_plant",
                "name": props.get("name", "Unknown"),
                "properties": props,
            })
    except Exception as exc:
        logger.warning("Energy data unavailable: %s", exc)

    # Get IMF indicators for forward-looking GDP growth rates
    imf_growth_context = {}
    try:
        imf_data = pipeline_bridge.get_imf_indicators()
        imf_indicators = imf_data.get("indicators", {})
        if isinstance(imf_indicators, dict):
            for country_key, data in imf_indicators.items():
                if isinstance(data, dict):
                    gdp_growth = data.get("gdp_growth", data.get("real_gdp_growth", None))
                    if gdp_growth is not None:
                        try:
                            imf_growth_context[country_key] = {
                                "gdp_growth_pct": float(gdp_growth),
                                "source": "IMF World Economic Outlook",
                            }
                        except (ValueError, TypeError):
                            pass
        logger.info("IMF growth indicators obtained for %d countries", len(imf_growth_context))
    except Exception as exc:
        logger.warning("IMF indicators unavailable: %s", exc)

    # Extract GDP growth rates from WB data if available
    country_growth_rates: dict[str, float] = {}
    if wb_indicators:
        # WB data structure varies — try to extract GDP growth per country
        if isinstance(wb_indicators, dict):
            for country_key, data in wb_indicators.items():
                if isinstance(data, dict):
                    gdp_growth = data.get("gdp_growth", data.get("GDP_growth", None))
                    if gdp_growth is not None:
                        try:
                            country_growth_rates[country_key] = float(gdp_growth) / 100.0
                        except (ValueError, TypeError):
                            pass

    detections = infra.get("detections", [])

    # Project demand for each non-generation facility
    trajectories = []
    total_current = 0.0
    total_y5 = 0.0
    total_y10 = 0.0
    total_y20 = 0.0
    generation_excluded = 0

    for i, det in enumerate(detections):
        det_type = det.get("type", "other")

        if det_type == "power_plant":
            generation_excluded += 1
            continue

        props = det.get("properties", {})
        country = props.get("country", props.get("addr:country", "Unknown"))

        # Determine sector and base demand
        sector = {
            "port_facility": "Industrial",
            "airport": "Industrial",
            "industrial_zone": "Industrial",
            "mineral_site": "Mining",
            "rail_network": "Industrial",
            "border_crossing": "Industrial",
        }.get(det_type, "Other")

        # Estimate current demand using same benchmarks as calculate_current_demand
        base_mw_map = {
            "port_facility": 20.0, "airport": 15.0, "industrial_zone": 30.0,
            "mineral_site": 25.0, "rail_network": 5.0, "border_crossing": 2.0,
        }
        current_mw = base_mw_map.get(det_type, 5.0)

        # Growth rate: prefer IMF forward-looking data, then WB data, then sector default
        imf_rate = None
        if country in imf_growth_context:
            try:
                imf_rate = imf_growth_context[country]["gdp_growth_pct"] / 100.0
            except (KeyError, TypeError):
                pass
        growth_rate = imf_rate or country_growth_rates.get(country, SECTOR_GROWTH_RATES.get(sector, 0.04))

        # Apply sector multiplier on top of GDP growth
        sector_multiplier = {
            "Industrial": 1.2, "Mining": 1.0, "Digital": 2.5,
            "Agriculture": 1.1, "Other": 1.0,
        }.get(sector, 1.0)

        effective_rate = growth_rate * sector_multiplier

        y5 = _project_demand(current_mw, effective_rate, 5)
        y10 = _project_demand(current_mw, effective_rate, 10)
        y20 = _project_demand(current_mw, effective_rate, 20)

        trajectory = {
            "anchor_id": f"AL_ANC_{i + 1:03d}",
            "detection_id": det.get("detection_id", f"DET-{i + 1:03d}"),
            "entity_name": det.get("name", "Unknown"),
            "country": country,
            "sector": sector,
            "current_mw": current_mw,
            "year_5_mw": y5,
            "year_10_mw": y10,
            "year_20_mw": y20,
            "growth_rate_applied": round(effective_rate, 3),
            "growth_source": (
                "IMF WEO" if country in imf_growth_context
                else "World Bank GDP" if country in country_growth_rates
                else "Sector default"
            ),
        }
        trajectories.append(trajectory)

        total_current += current_mw
        total_y5 += y5
        total_y10 += y10
        total_y20 += y20

    growth_pct = round((total_y20 / total_current - 1) * 100, 0) if total_current > 0 else 0

    response = {
        "aggregate_trajectory": {
            "current_mw": round(total_current, 1),
            "year_5_mw": round(total_y5, 1),
            "year_10_mw": round(total_y10, 1),
            "year_20_mw": round(total_y20, 1),
            "overall_growth_pct": f"{growth_pct}%",
        },
        "anchor_trajectories": trajectories,
        "generation_assets_excluded": generation_excluded,
        "wb_indicators_used": bool(wb_indicators),
        "imf_growth_context": imf_growth_context if imf_growth_context else {},
        "country_growth_rates": {k: round(v, 3) for k, v in country_growth_rates.items()},
        "data_sources": [
            "IMF World Economic Outlook" if imf_growth_context else "IMF (unavailable)",
            "World Bank" if wb_indicators else "Sector defaults (World Bank unavailable)",
            "OpenStreetMap",
            "USGS Minerals",
        ],
        "message": (
            f"20-year demand trajectories modeled for {len(trajectories)} anchor loads. "
            f"Corridor demand projected from {total_current:,.1f} MW to {total_y20:,.1f} MW "
            f"({growth_pct}% growth over 20 years). "
            + (f"IMF forward-looking growth rates used for {len(imf_growth_context)} countries. " if imf_growth_context else "")
            + (f"World Bank GDP indicators used for country-specific rates." if wb_indicators else "Sector default growth rates applied.")
        ),
    }

    return Command(update={"messages": [ToolMessage(
        content=json.dumps(response), tool_call_id=runtime.tool_call_id,
    )]})
