import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("opp_entity_resolution", description=TOOL_DESCRIPTION)
def opp_entity_resolution_tool( runtime: ToolRuntime) -> Command:
    """
    Mock tool: match facilities/companies to geo detections; dedupe.
    """
    result = {
        "status": "ok",
        "step": "entity_resolution",
        "resolved_entities": 50,
        "duplicates_removed": 5,
        
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

