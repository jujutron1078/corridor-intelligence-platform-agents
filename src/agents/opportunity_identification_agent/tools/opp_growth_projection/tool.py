import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("opp_growth_projection", description=TOOL_DESCRIPTION)
def opp_growth_projection_tool( runtime: ToolRuntime) -> Command:
    """
    Mock tool: project demand to 2035 with scenarios.
    """
    result = {
        "status": "ok",
        "step": "growth_projection",
        "projected_total_mw_range_2035": [2650, 3880],
        "scenarios": ["low", "base", "high"],
        
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

