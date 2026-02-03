import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("stake_risk_register", description=TOOL_DESCRIPTION)
def stake_risk_register_tool(config: dict, runtime: ToolRuntime) -> Command:
    """
    Mock tool: political/social/coordination risks and mitigations.
    """
    result = {
        "status": "ok",
        "step": "risk_register",
        "risk_count": 10,
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

