import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import DebtTermInput


@tool("optimize_debt_terms", description=TOOL_DESCRIPTION)
def optimize_debt_terms_tool(
    payload: DebtTermInput, runtime: ToolRuntime
) -> Command:
    """Aligns debt repayment with infrastructure cash flow patterns."""

    # In a real-world scenario, this tool would:
    # 1. Test 15-year vs 25-year tenors.
    # 2. Model a 5-year grace period during construction.
    # 3. Create a 'Sculpted' amortization profile to match industrial demand growth.

    response = {
        "optimized_terms": {
            "tenor_years": 25,
            "grace_period_years": 5,
            "interest_rate_concessional": "3.0%",
            "interest_rate_commercial": "6.5%"
        },
        "message": "Debt terms optimized. 25-year tenor confirmed to maintain 1.5x DSCR."
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
