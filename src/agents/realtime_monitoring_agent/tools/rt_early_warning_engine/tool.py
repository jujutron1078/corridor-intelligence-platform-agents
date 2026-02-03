import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("rt_early_warning_engine", description=TOOL_DESCRIPTION)
def rt_early_warning_engine_tool(config: dict, runtime: ToolRuntime) -> Command:
    """
    Mock tool: detect overruns, delays, and ranked risks.
    """
    result = {
        "status": "ok",
        "step": "early_warning_engine",
        "alerts": [
            {"id": "a1", "severity": "medium", "issue": "slight schedule slippage"},
        ],
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

