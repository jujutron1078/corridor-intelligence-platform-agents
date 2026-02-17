import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import CreditEnhancementInput


@tool("model_credit_enhancement", description=TOOL_DESCRIPTION)
def model_credit_enhancement_tool(
    payload: CreditEnhancementInput, runtime: ToolRuntime
) -> Command:
    """Models the impact of risk mitigation instruments on the final WACC."""

    # In a real-world scenario, this tool would:
    # 1. Calculate the 'Premium' for Political Risk Insurance.
    # 2. Model a First-Loss Guarantee to lower commercial interest rates by 150-200 bps.
    # 3. Assess the impact on WACC after adding enhancement costs.

    response = {
        "enhancement_plan": {
            "instrument": "Partial Credit Guarantee (PCG)",
            "provider": "GuarantCo / MIGA",
            "cost_bps": 120,
            "commercial_debt_reduction_bps": 210
        },
        "final_wacc_impact": "-0.45%",
        "message": "Credit enhancement modeling complete. PCG recommended to attract commercial banks."
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
