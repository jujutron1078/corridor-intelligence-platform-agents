from __future__ import annotations

import json
import logging

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from src.adapters.pipeline_bridge import pipeline_bridge as pb

from .description import TOOL_DESCRIPTION
from .schema import ClimateRiskInput

logger = logging.getLogger("corridor.agent.geospatial.climate_risk")


@tool(description=TOOL_DESCRIPTION, args_schema=ClimateRiskInput)
def climate_risk_assessment(
    tool_call_id: ToolRuntime,
    corridor_id: str,
    aoi_geojson: dict | None = None,
    country_iso3: str | None = None,
    hazards: list[str] | None = None,
    coastal_return_period: int = 100,
) -> Command:
    """Collect climate hazard scores for the corridor."""
    hazards = hazards or ["drought", "heat", "coastal_flood"]
    payload: dict[str, dict] = {
        "corridor_id": corridor_id,
        "hazards_requested": hazards,
    }
    if "drought" in hazards:
        payload["drought_risk"] = pb.get_drought_data(aoi_geojson)
    if "heat" in hazards:
        payload["heat_risk"] = pb.get_heat_risk_data(aoi_geojson)
    if "coastal_flood" in hazards:
        payload["coastal_flood_risk"] = pb.get_coastal_flood_data(
            aoi_geojson, return_period=coastal_return_period
        )
    if "composite" in hazards and country_iso3:
        payload["composite_climate_risk"] = pb.get_composite_climate_risk(country_iso3)

    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=json.dumps(payload, default=str),
                    tool_call_id=tool_call_id.tool_call_id,
                )
            ]
        }
    )
