import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("stake_entity_resolution", description=TOOL_DESCRIPTION)
def stake_entity_resolution_tool( runtime: ToolRuntime) -> Command:
    """
    Mock tool: dedupe names, roles, and org hierarchies.
    """
    result = {
        "status": "ok",
        "step": "entity_resolution",
        "unique_stakeholders": 170,
        
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

