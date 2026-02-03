import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("fin_base_model", description=TOOL_DESCRIPTION)
def fin_base_model_tool(config: dict, runtime: ToolRuntime) -> Command:
    """
    Mock tool: build base project cashflows.
    """
    result = {
        "status": "ok",
        "step": "base_financial_model",
        "model_id": "mock_base_model_v1",
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

