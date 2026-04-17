import json
import logging

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .schema import DefineCorridorInput
from .description import TOOL_DESCRIPTION

logger = logging.getLogger("corridor.agent.geospatial.define_corridor")


@tool("define_corridor", description=TOOL_DESCRIPTION)
def define_corridor_tool(
    payload: DefineCorridorInput, runtime: ToolRuntime
) -> Command:
    """Creates a geographic bounding polygon (corridor) between two points."""
    from src.adapters.pipeline_bridge import pipeline_bridge

    try:
        response = pipeline_bridge.define_corridor(
            buffer_width_km=payload.buffer_width_km
        )
    except Exception as exc:
        logger.error("Define corridor failed: %s", exc)
        response = {
            "error": str(exc),
            "corridor_id": None,
            "message": "Corridor definition failed. Check AOI configuration.",
        }

    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=json.dumps(response),
                    tool_call_id=runtime.tool_call_id,
                )
            ]
        }
    )
