import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("infra_substation_siting", description=TOOL_DESCRIPTION)
def infra_substation_siting_tool( runtime: ToolRuntime) -> Command:
    """
    Mock tool: cluster anchor loads and place substations.
    """
    result = {
        "status": "ok",
        "step": "substation_siting",
        "substation_count": 10,
        
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

