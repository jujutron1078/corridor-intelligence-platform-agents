import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("econ_input_validator", description=TOOL_DESCRIPTION)
def econ_input_validator_tool(payload: dict, runtime: ToolRuntime) -> Command:
    """
    Mock tool: require anchor load portfolio; accept preliminary CAPEX.
    """
    result = {
        "status": "ok",
        "step": "input_validator",
        "anchor_loads_available": True,
        "capex_is_preliminary": True,
        "echo": payload,
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


