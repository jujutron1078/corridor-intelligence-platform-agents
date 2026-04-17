"""
Corridor Data Tool — gives agents direct access to ALL platform data.

Wraps the backend API services so agents can query real corridor data
instead of using hardcoded benchmarks or asking clarifying questions.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import CORRIDOR_DATA_TOOL_DESCRIPTION

logger = logging.getLogger("corridor.agents.tools.corridor_data")


def _call_service(function_name: str, params: dict[str, Any]) -> dict[str, Any]:
    """Call the appropriate backend service function and return results."""

    try:
        # Economic indicators
        if function_name == "get_country_summary":
            from src.api.services import worldbank_service
            return worldbank_service.get_country_summary(params.get("country"))

        if function_name == "get_country_indicators":
            from src.api.services import worldbank_service
            indicator = params.get("indicator", "GDP")
            return worldbank_service.get_indicator(
                indicator,
                params.get("country"),
                params.get("start_year"),
                params.get("end_year"),
            )

        # Trade
        if function_name == "get_trade_flows":
            from src.api.services import trade_service
            country = params.get("country")
            commodity = params.get("commodity")
            if not commodity:
                return {"error": "'commodity' is required for get_trade_flows"}
            if not country:
                # Query all 5 corridor countries
                results = []
                for iso3 in ["NGA", "BEN", "TGO", "GHA", "CIV"]:
                    r = trade_service.get_trade_flows(iso3, commodity)
                    if r.get("data"):
                        results.append(r)
                return {"commodity": commodity, "countries": results, "total_countries": len(results)}
            return trade_service.get_trade_flows(country, commodity)

        if function_name == "get_commodity_prices":
            from src.api.services import trade_service
            commodity = params.get("commodity")
            if not commodity:
                return {"error": "'commodity' is required for get_commodity_prices"}
            return trade_service.get_commodity_prices(
                commodity,
                params.get("start_year"),
                params.get("end_year"),
            )

        if function_name == "get_value_chain":
            from src.api.services import trade_service
            commodity = params.get("commodity")
            if not commodity:
                return {"error": "'commodity' is required for get_value_chain"}
            return trade_service.get_value_chain(commodity)

        # Infrastructure
        if function_name == "get_infrastructure":
            from src.api.services import osm_service
            return osm_service.get_infrastructure()

        if function_name == "get_power_plants":
            from src.api.services import energy_service
            return energy_service.get_power_plants(
                params.get("fuel"), params.get("country"), params.get("min_capacity_mw")
            )

        if function_name == "get_roads":
            from src.api.services import osm_service
            tiers = params.get("tiers")
            return osm_service.get_roads(tiers)

        # Projects
        if function_name in ("get_projects", "get_projects_enriched"):
            from src.api.services import projects_enriched_service
            return projects_enriched_service.get_projects(
                params.get("country"), params.get("sector"), params.get("status")
            )

        if function_name == "get_projects_summary":
            from src.api.services import projects_enriched_service
            return projects_enriched_service.get_summary()

        # Conflict
        if function_name == "get_conflict_events":
            from src.api.services import acled_service
            return acled_service.get_conflict_events(
                params.get("country"), params.get("year"), params.get("event_type")
            )

        # Minerals
        if function_name == "get_minerals":
            from src.api.services import mineral_service
            return mineral_service.get_minerals(params.get("commodity"), params.get("status"))

        if function_name == "get_economic_anchors":
            from src.api.services import mineral_service
            return mineral_service.get_economic_anchors()

        # Social facilities
        if function_name == "get_social_facilities":
            from src.api.services import osm_service
            return osm_service.get_social_facilities(params.get("type"))

        # Geospatial / GEE
        if function_name == "get_nightlights":
            from src.api.services import gee_service
            return gee_service.get_nightlights(params.get("year", 2023), params.get("month", 6))

        if function_name == "get_population":
            from src.api.services import gee_service
            return gee_service.get_population(params.get("year", 2020))

        if function_name == "get_landcover":
            from src.api.services import gee_service
            return gee_service.get_landcover()

        if function_name == "get_economic_index":
            from src.api.services import gee_service
            return gee_service.get_economic_index(params.get("year", 2023), params.get("month", 6))

        # Livestock
        if function_name == "get_livestock":
            from src.api.services import livestock_service
            return livestock_service.get_livestock(params.get("species"))

        # Connectivity
        if function_name == "get_connectivity":
            from src.api.services import connectivity_service
            result = connectivity_service.get_connectivity(params.get("type", "mobile"))
            # Don't return the full GeoJSON features (too large), just summary
            summary = result.get("summary", {})
            return {"network_type": result.get("network_type"), "summary": summary, "total_tiles": len(result.get("features", []))}

        # Policy
        if function_name == "get_policies":
            from src.api.services import policy_service
            return policy_service.get_policies(params.get("country"), params.get("category"))

        if function_name == "get_policy_comparison":
            from src.api.services import policy_service
            return policy_service.get_comparison()

        if function_name == "get_governance":
            from src.api.services import policy_service
            return policy_service.get_governance()

        # Agriculture
        if function_name == "get_agriculture":
            from src.api.services import agriculture_enriched_service
            return agriculture_enriched_service.get_crops(params.get("country"), params.get("crop"))

        # Tourism
        if function_name == "get_tourism":
            from src.api.services import tourism_service
            return tourism_service.get_comparison()

        # Manufacturing
        if function_name == "get_manufacturing":
            from src.api.services import manufacturing_service
            return manufacturing_service.get_companies(params.get("country"), params.get("sector"))

        return {"error": f"Unknown function: {function_name}"}

    except Exception as exc:
        logger.error("corridor_data_tool error calling %s: %s", function_name, exc)
        return {"error": str(exc)}


def _truncate_geojson(data: Any, max_features: int = 50) -> Any:
    """Truncate large GeoJSON to avoid context overflow."""
    if isinstance(data, dict):
        if data.get("type") == "FeatureCollection" and isinstance(data.get("features"), list):
            total = len(data["features"])
            if total > max_features:
                data = {
                    **data,
                    "features": data["features"][:max_features],
                    "_truncated": True,
                    "_total_features": total,
                    "_shown_features": max_features,
                }
        # Also truncate nested GeoJSON
        for key, val in data.items():
            if isinstance(val, dict) and val.get("type") == "FeatureCollection":
                data[key] = _truncate_geojson(val, max_features)
    return data


@tool(description=CORRIDOR_DATA_TOOL_DESCRIPTION)
def query_corridor_data(
    function_name: str,
    parameters: dict | None = None,
    runtime: ToolRuntime = None,
) -> Command:
    """
    Query corridor platform data. Use function_name and parameters to call
    any of the available data functions listed in the description.
    """
    params = parameters or {}
    logger.info("query_corridor_data: %s(%s)", function_name, params)

    result = _call_service(function_name, params)

    # Truncate large results to avoid context overflow
    result = _truncate_geojson(result)

    # Serialize
    try:
        content = json.dumps(result, default=str, ensure_ascii=False)
        # Hard limit to prevent context explosion
        if len(content) > 30000:
            content = content[:30000] + '\n... [truncated, too large for context]'
    except Exception:
        content = str(result)[:30000]

    tool_call_id = runtime.tool_call_id if runtime else "corridor_data"

    return Command(update={"messages": [ToolMessage(
        content=content,
        tool_call_id=tool_call_id,
    )]})
