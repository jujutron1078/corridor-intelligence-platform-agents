import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("rt_recommendation_engine", description=TOOL_DESCRIPTION)
def rt_recommendation_engine_tool( runtime: ToolRuntime) -> Command:
    """
    Mock tool: suggest mitigations and resequencing options.
    """
    result = {
        "status": "ok",
        "step": "recommendation_engine",
        "recommendations": ["increase night shifts on critical segment"],
        
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

