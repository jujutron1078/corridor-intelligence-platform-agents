import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("fin_optimizer", description=TOOL_DESCRIPTION)
def fin_optimizer_tool(config: dict, runtime: ToolRuntime) -> Command:
    """
    Mock tool: choose capital stack meeting IRR/DSCR constraints.
    """
    result = {
        "status": "ok",
        "step": "optimizer",
        "recommended_scenario_id": "scenario_07",
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

