import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("rt_kpi_calculator", description=TOOL_DESCRIPTION)
def rt_kpi_calculator_tool( runtime: ToolRuntime) -> Command:
    """
    Mock tool: compute earned value, schedule and budget variance, and covenant checks.
    """
    result = {
        "status": "ok",
        "step": "kpi_calculator",
        "kpis": {
            "spi": 0.95,
            "cpi": 0.98,
            "burn_rate_vs_plan": 1.05,
        },
        
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

