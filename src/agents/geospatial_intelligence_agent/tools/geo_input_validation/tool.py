import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("geo_input_validation", description=TOOL_DESCRIPTION)
def geo_input_validation_tool(payload: dict, runtime: ToolRuntime) -> Command:
    """
    Mock tool: validate corridor geometry, buffer distance, time window, and target asset types.
    """
    result = {
        "status": "ok",
        "step": "input_validation",
        "details": "Inputs validated successfully (mock).",
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

