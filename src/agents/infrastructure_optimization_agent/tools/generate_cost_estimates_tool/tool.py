import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import CostEstimationInput


@tool("generate_cost_estimates", description=TOOL_DESCRIPTION)
def generate_cost_estimates_tool(
    payload: CostEstimationInput, runtime: ToolRuntime
) -> Command:
    """Calculates total project CAPEX ($730M-$1,005M) and annual OPEX."""

    # In a real-world scenario, this tool would:
    # 1. Use unit costs (e.g., $450k/km for 400kV line, $15M per substation).
    # 2. Calculate OPEX as a percentage (typically 1-2%) of total CAPEX.
    # 3. Adjust for local labor and logistics costs in each country.

    response = {
        "cost_summary": {
            "total_capex_usd": 865000000,
            "line_costs": 487000000,
            "substation_costs": 240000000,
            "other_civil_and_eia": 138000000,
            "annual_opex_usd": 18500000,
        },
        "capex_range": "$730M - $1,005M",
        "message": "Detailed cost estimates generated based on 400kV Quad-bundle ACSR specs.",
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
