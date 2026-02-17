import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import FinancialModelInput


@tool("build_financial_model", description=TOOL_DESCRIPTION)
def build_financial_model_tool(
    payload: FinancialModelInput, runtime: ToolRuntime
) -> Command:
    """Calculates core financial metrics for the project lifecycle."""

    # In a real-world scenario, this tool would:
    # 1. Build a full 3-statement financial model (Income, Balance Sheet, Cash Flow).
    # 2. Calculate annual DSCR to ensure bankability (targeting 1.4-1.8x).
    # 3. Determine the NPV and Payback Period based on the WACC from Tool 2.

    response = {
        "metrics": {
            "equity_irr": "14.2%",
            "project_irr": "10.1%",
            "net_present_value_usd": 420000000,
            "min_dscr": 1.55,
            "payback_period_years": 12
        },
        "status": "Investor-grade model ready",
        "message": "Detailed DCF model complete. Project meets target return thresholds."
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
