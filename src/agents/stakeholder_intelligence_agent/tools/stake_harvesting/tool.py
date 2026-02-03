import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("stake_harvesting", description=TOOL_DESCRIPTION)
def stake_harvesting_tool(config: dict, runtime: ToolRuntime) -> Command:
    """
    Mock tool: collect stakeholder candidates across categories.
    """
    result = {
        "status": "ok",
        "step": "stakeholder_harvesting",
        "candidate_count": 180,
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

