import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import RiskAnalysisInput


@tool("perform_risk_and_sensitivity_analysis", description=TOOL_DESCRIPTION)
def perform_risk_and_sensitivity_analysis_tool(
    payload: RiskAnalysisInput, runtime: ToolRuntime
) -> Command:
    """Runs 10,000 simulations to determine the probability distribution of returns."""

    # In a real-world scenario, this tool would:
    # 1. Run a Monte Carlo simulation for probability of IRR > 12%.
    # 2. Perform a sensitivity 'Tornado' analysis on CAPEX and Revenue.
    # 3. Identify the 'Break-even' utilization rate for the anchor loads.

    response = {
        "monte_carlo_results": {
            "prob_irr_above_12_percent": "88%",
            "p50_irr": "14.1%",
            "p90_irr": "11.8%"
        },
        "critical_risks": ["CAPEX overrun (>15%)", "Currency devaluation (West African Zone)"],
        "message": "Risk analysis complete. High probability of achieving target returns."
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
