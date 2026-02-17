import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import PovertyReductionInput


@tool("assess_poverty_reduction", description=TOOL_DESCRIPTION)
def assess_poverty_reduction_tool(
    payload: PovertyReductionInput, runtime: ToolRuntime
) -> Command:
    """Models electricity access expansion and resulting income effects."""

    # In a real-world scenario, this tool would:
    # 1. Correlate energy access with increased household productivity hours.
    # 2. Apply income-growth coefficients to the newly electrified populations.
    # 3. Project the number of individuals crossing the $2.15/day threshold.

    response = {
        "poverty_reduction_impact": {
            "additional_people_electrified": 1500000,
            "estimated_poverty_reduction_count": 450000,
            "avg_household_income_gain": "18%",
        },
        "message": "Poverty reduction metrics modeled against baseline electrification data.",
    }

    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=json.dumps(response), tool_call_id=runtime.tool_call_id
                )
            ]
        }
    )
