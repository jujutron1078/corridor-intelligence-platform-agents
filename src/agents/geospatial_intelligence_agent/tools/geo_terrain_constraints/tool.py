import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("geo_terrain_constraints", description=TOOL_DESCRIPTION)
def geo_terrain_constraints_tool(config: dict, runtime: ToolRuntime) -> Command:
    """
    Mock tool: compute slope, crossings, and protected-area intersections.
    """
    result = {
        "status": "ok",
        "step": "terrain_constraints",
        "summary": {
            "avg_slope_pct": 4.5,
            "river_crossings": 7,
            "protected_area_intersections": 2,
        },
        "echo": config,
    }
    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=json.dumps(result),
                    tool_call_id=runtime.tool_call_id,
                )
            ]
        }
    )

