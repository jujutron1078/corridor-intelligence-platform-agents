import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("geo_route_generator", description=TOOL_DESCRIPTION)
def geo_route_generator_tool(config: dict, runtime: ToolRuntime) -> Command:
    """
    Mock tool: generate 50–100 route variants with basic scoring.
    """
    result = {
        "status": "ok",
        "step": "route_generator",
        "routes": [
            {"id": "route_shortest", "variant": "shortest_distance", "score": 0.7},
            {"id": "route_lowest_risk", "variant": "lowest_risk", "score": 0.82},
            {"id": "route_high_colocation", "variant": "highest_colocation", "score": 0.8},
        ],
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

