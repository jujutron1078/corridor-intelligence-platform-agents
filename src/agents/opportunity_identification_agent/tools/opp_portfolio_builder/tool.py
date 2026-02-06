import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("opp_portfolio_builder", description=TOOL_DESCRIPTION)
def opp_portfolio_builder_tool(runtime: ToolRuntime) -> Command:
    """
    Mock tool: produce final catalog of 45–57 anchor loads.
    """
    result = {
        "status": "ok",
        "step": "portfolio_builder",
        "anchor_load_count": 50,
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

