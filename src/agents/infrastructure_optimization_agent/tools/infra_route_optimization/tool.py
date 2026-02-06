import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("infra_route_optimization", description=TOOL_DESCRIPTION)
def infra_route_optimization_tool( runtime: ToolRuntime) -> Command:
    """
    Mock tool: evaluate and refine route candidates to top 5–10.
    """
    result = {
        "status": "ok",
        "step": "route_optimization",
        "recommended_route_ids": [f"route_{i}" for i in range(1, 6)],
        
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

