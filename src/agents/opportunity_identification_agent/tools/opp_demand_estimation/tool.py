import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("opp_demand_estimation", description=TOOL_DESCRIPTION)
def opp_demand_estimation_tool( runtime: ToolRuntime) -> Command:
    """
    Mock tool: estimate current MW and load factors.
    """
    result = {
        "status": "ok",
        "step": "demand_estimation",
        "current_total_mw_range": [950, 1300],
        
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

