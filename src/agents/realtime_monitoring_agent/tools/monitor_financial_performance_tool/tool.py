import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import FinancialTrackingInput


@tool("monitor_financial_performance", description=TOOL_DESCRIPTION)
def monitor_financial_performance_tool(
    payload: FinancialTrackingInput, runtime: ToolRuntime
) -> Command:
    """Tracks budget variance, revenue performance, and bankability covenants."""

    # In a real-world scenario, this tool would:
    # 1. Calculate Burn Rate and Cost Performance Index (CPI).
    # 2. Verify DSCR levels (targeting 1.82x) to ensure no breach of DFI loan terms.
    # 3. Monitor currency fluctuations impacting cross-border debt repayments.

    response = {
        "financial_status": {
            "capex_spent_usd": 420000000,
            "budget_variance": "-5% (Under Budget)",
            "actual_revenue_y3": 48000000,
            "dscr_actual": 1.82
        },
        "covenant_compliance": "Fully Compliant",
        "message": "Financial performance is healthy; revenue exceeding projections by 7%."
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
