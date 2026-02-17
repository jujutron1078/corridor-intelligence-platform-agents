import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import GDPMultiplierInput


@tool("calculate_gdp_multipliers", description=TOOL_DESCRIPTION)
def calculate_gdp_multipliers_tool(
    payload: GDPMultiplierInput, runtime: ToolRuntime
) -> Command:
    """Calculates total GDP impact including direct, indirect, and induced effects."""

    # In a real-world scenario, this tool would:
    # 1. Apply a 1.8x to 2.2x multiplier typical for infrastructure in West Africa.
    # 2. Calculate 'Direct' impact from construction payroll and materials.
    # 3. Calculate 'Indirect' impact from supply chain and industrial off-take.
    # 4. Calculate 'Induced' impact from household spending by newly employed workers.

    response = {
        "status": "GDP Analysis Complete",
        "total_gdp_impact_usd": payload.total_capex * 2.1,
        "impact_breakdown": {
            "direct_impact": "30%",
            "indirect_impact": "45%",
            "induced_impact": "25%",
        },
        "regional_multiplier": 2.1,
        "message": "GDP impact quantified using corridor-specific Input-Output frameworks.",
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
