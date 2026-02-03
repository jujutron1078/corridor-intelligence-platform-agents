import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("fin_input_validator", description=TOOL_DESCRIPTION)
def fin_input_validator_tool(payload: dict, runtime: ToolRuntime) -> Command:
    """
    Mock tool: require CAPEX/OPEX, demand/revenue, and impact scores.
    """
    result = {
        "status": "ok",
        "step": "input_validator",
        "capex_available": True,
        "opex_available": True,
        "demand_available": True,
        "impact_scores_available": True,
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

