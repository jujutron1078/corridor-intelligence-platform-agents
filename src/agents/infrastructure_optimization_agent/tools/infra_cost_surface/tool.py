import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("infra_cost_surface", description=TOOL_DESCRIPTION)
def infra_cost_surface_tool(config: dict, runtime: ToolRuntime) -> Command:
    """
    Mock tool: build multi-layer cost surface and segment attributes.
    """
    result = {
        "status": "ok",
        "step": "cost_surface",
        "layers": ["terrain", "land", "environmental", "social_risk"],
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

