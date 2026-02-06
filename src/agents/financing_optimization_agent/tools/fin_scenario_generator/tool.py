import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("fin_scenario_generator", description=TOOL_DESCRIPTION)
def fin_scenario_generator_tool( runtime: ToolRuntime) -> Command:
    """
    Mock tool: produce 20–30 blended finance structures.
    """
    result = {
        "status": "ok",
        "step": "scenario_generator",
        "scenario_count": 25,
        
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

