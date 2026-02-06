import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("opp_input_validator", description=TOOL_DESCRIPTION)
def opp_input_validator_tool(payload: dict, runtime: ToolRuntime) -> Command:
    """
    Mock tool: ensure Geo detections exist (or accept partial).
    """

    # TODO: Implement the tool logic
    result = {
        "status": "ok",
        "step": "input_validator",
        "geo_detections_available": True,
        "notes": "Using mock geospatial detections.",
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

