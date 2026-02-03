import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("econ_multiplier_model", description=TOOL_DESCRIPTION)
def econ_multiplier_model_tool(config: dict, runtime: ToolRuntime) -> Command:
    """
    Mock tool: apply corridor-specific multipliers.
    """
    result = {
        "status": "ok",
        "step": "multiplier_model",
        "multiplier_range": [1.8, 2.2],
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


