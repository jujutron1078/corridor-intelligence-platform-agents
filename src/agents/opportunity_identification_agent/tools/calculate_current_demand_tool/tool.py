import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import CurrentDemandInput


@tool("calculate_current_demand", description=TOOL_DESCRIPTION)
def calculate_current_demand_tool(
    payload: CurrentDemandInput, runtime: ToolRuntime
) -> Command:
    """Calculates immediate resource demand for each anchor load."""

    # In a real-world scenario, this tool would:
    # 1. Apply energy intensity benchmarks (e.g., kW per hectare for agro-processing).
    # 2. Correlate facility footprint (from Agent 1) with known production capacities.
    # 3. Aggregate current demand to determine substation sizing requirements.

    response = {
        "total_current_mw": 1845.5,
        "demand_profiles": [
            {
                "anchor_id": "AL_ANC_042",
                "current_mw": 45.0,
                "load_factor": 0.85,
                "reliability_class": "Critical"
            }
        ],
        "message": "Current demand profiles aggregated for identified loads."
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
