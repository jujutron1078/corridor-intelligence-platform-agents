import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("fin_monte_carlo_risk", description=TOOL_DESCRIPTION)
def fin_monte_carlo_risk_tool( runtime: ToolRuntime) -> Command:
    """
    Mock tool: stress test and sensitivity outputs.
    """
    result = {
        "status": "ok",
        "step": "monte_carlo_risk",
        "prob_meet_dscr": 0.85,
        "prob_meet_equity_irr": 0.78,
        
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

