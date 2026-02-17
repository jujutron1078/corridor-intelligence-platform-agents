import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import ScenarioAnalysisInput


@tool("perform_impact_scenario_analysis", description=TOOL_DESCRIPTION)
def perform_impact_scenario_analysis_tool(
    payload: ScenarioAnalysisInput, runtime: ToolRuntime
) -> Command:
    """Compares baseline vs project development trajectories."""

    # In a real-world scenario, this tool would:
    # 1. Run Monte Carlo simulations for 'No Project' vs 'With Project' scenarios.
    # 2. Visualize the 'GDP Delta' over a 20-year lifecycle analysis.
    # 3. Calculate the Opportunity Cost of non-investment.

    response = {
        "scenario_comparison": {
            "baseline_20_yr_gdp_growth": "4.2%",
            "enhanced_20_yr_gdp_growth": "6.8%",
            "total_value_add_usd": "7.5B annually by Year 10",
        },
        "confidence_interval": "95%",
        "message": "Comparative impact analysis complete.",
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
