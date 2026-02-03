import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("stake_engagement_planner", description=TOOL_DESCRIPTION)
def stake_engagement_planner_tool(config: dict, runtime: ToolRuntime) -> Command:
    """
    Mock tool: design phase plan and messaging per segment.
    """
    result = {
        "status": "ok",
        "step": "engagement_planner",
        "phases": ["discovery", "alignment", "commitments", "execution"],
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

