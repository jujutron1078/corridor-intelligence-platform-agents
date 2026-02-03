import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("econ_scenario_runner", description=TOOL_DESCRIPTION)
def econ_scenario_runner_tool(config: dict, runtime: ToolRuntime) -> Command:
    """
    Mock tool: run low/base/high scenarios with confidence intervals.
    """
    result = {
        "status": "ok",
        "step": "scenario_runner",
        "scenarios": [
            {"name": "low", "gdp_annual_usd_b": 4.7},
            {"name": "base", "gdp_annual_usd_b": 6.0},
            {"name": "high", "gdp_annual_usd_b": 7.5},
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


