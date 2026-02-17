import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import ScenarioGenerationInput


@tool("generate_financing_scenarios", description=TOOL_DESCRIPTION)
def generate_financing_scenarios_tool(
    payload: ScenarioGenerationInput, runtime: ToolRuntime
) -> Command:
    """Creates multiple blended finance structures to optimize project returns."""

    # In a real-world scenario, this tool would:
    # 1. Use combinatorial optimization to test different funding stacks.
    # 2. Calculate WACC for each scenario (targeting 5.5-7.5%).
    # 3. Flag scenarios that meet the 12-16% Equity IRR requirement.

    response = {
        "scenarios_generated": 25,
        "recommended_scenario": {
            "grants_usd": 120000000,
            "concessional_loans_usd": 450000000,
            "commercial_debt_usd": 295000000,
            "equity_usd": 150000000,
            "wacc": "6.2%"
        },
        "message": "25 scenarios generated. Scenario 12 offers the best balance of IRR and DSCR."
    }

    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=json.dumps(response),
                    tool_call_id=runtime.tool_call_id
                )
            ]
        }
    )
