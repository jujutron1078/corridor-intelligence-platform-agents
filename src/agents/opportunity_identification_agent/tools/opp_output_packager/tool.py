import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("opp_output_packager", description=TOOL_DESCRIPTION)
def opp_output_packager_tool(_: dict, runtime: ToolRuntime) -> Command:
    """
    Mock tool: write structured catalog and summary stats.
    """
    result = {
        "status": "ok",
        "step": "output_packager",
        "artifacts": ["anchor_loads.json", "portfolio_summary.json"],
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

