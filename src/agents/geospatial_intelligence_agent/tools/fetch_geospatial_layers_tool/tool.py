import json
import logging

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import FetchLayersInput

logger = logging.getLogger("corridor.agent.geospatial.fetch_layers")


@tool("fetch_geospatial_layers", description=TOOL_DESCRIPTION)
def fetch_geospatial_layers_tool(
    payload: FetchLayersInput, runtime: ToolRuntime
) -> Command:
    """Fetches and processes geospatial layers for the specified corridor."""
    from src.adapters.pipeline_bridge import pipeline_bridge

    layers = getattr(payload, "layers_requested", None) or [
        "satellite", "dem", "land_use", "protected_areas"
    ]

    try:
        response = pipeline_bridge.get_geospatial_layers(layers=layers)

        # Enrich with OSM infrastructure summary
        try:
            infra = pipeline_bridge.get_infrastructure_detections()
            response["data_inventory"]["osm_infrastructure"] = {
                "detection_count": infra.get("detection_count", 0),
                "source": "OpenStreetMap + USGS",
            }
        except Exception:
            pass

    except Exception as exc:
        logger.error("Fetch geospatial layers failed: %s", exc)
        response = {
            "error": str(exc),
            "corridor_id": "AL_CORRIDOR_001",
            "status": "Layer fetch failed",
            "message": "GEE service may not be initialized. Check credentials.",
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
