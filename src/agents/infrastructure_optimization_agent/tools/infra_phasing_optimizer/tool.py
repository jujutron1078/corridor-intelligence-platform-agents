import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("infra_phasing_optimizer", description=TOOL_DESCRIPTION)
def infra_phasing_optimizer_tool(config: dict, runtime: ToolRuntime) -> Command:
    """
    Mock tool: align phases with highest-demand clusters first.
    """
    result = {
        "status": "ok",
        "step": "phasing_optimizer",
        "phases": [
            {"phase": 1, "description": "High-demand clusters"},
            {"phase": 2, "description": "Secondary clusters"},
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

