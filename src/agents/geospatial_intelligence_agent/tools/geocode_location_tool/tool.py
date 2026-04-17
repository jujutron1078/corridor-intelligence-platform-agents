import json
import logging

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import GeocodeLocationInput

logger = logging.getLogger("corridor.agent.geospatial.geocode")


@tool("geocode_location", description=TOOL_DESCRIPTION)
def geocode_location_tool(
    payload: GeocodeLocationInput, runtime: ToolRuntime
) -> Command:
    """Resolve place names to coordinates using corridor nodes."""
    from src.adapters.pipeline_bridge import pipeline_bridge

    names = [loc.name for loc in payload.locations]

    try:
        response = pipeline_bridge.geocode_location(names)
    except Exception as exc:
        logger.error("Geocode failed: %s", exc)
        response = {
            "error": str(exc),
            "resolved_locations": [],
            "message": "Geocoding service unavailable. Check pipeline initialization.",
        }

    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=json.dumps(response), tool_call_id=runtime.tool_call_id
                )
            ]
        }
    )
