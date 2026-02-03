import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("opp_bankability_scorer", description=TOOL_DESCRIPTION)
def opp_bankability_scorer_tool(config: dict, runtime: ToolRuntime) -> Command:
    """
    Mock tool: assign bankability scores.
    """
    result = {
        "status": "ok",
        "step": "bankability_scorer",
        "score_distribution": {
            "high": 20,
            "medium": 25,
            "low": 10,
        },
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

