import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("infra_input_validator", description=TOOL_DESCRIPTION)
def infra_input_validator_tool(payload: dict, runtime: ToolRuntime) -> Command:
    """
    Mock tool: confirm Geo route set and anchor loads are available.
    """
    result = {
        "status": "ok",
        "step": "input_validator",
        "routes_available": True,
        "anchor_loads_available": True,
        "echo": payload,
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

