import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import GapAnalysisInput


@tool("economic_gap_analysis", description=TOOL_DESCRIPTION)
def economic_gap_analysis_tool(
    payload: GapAnalysisInput, runtime: ToolRuntime
) -> Command:
    """Identifies underserved areas with high economic potential."""

    # In a real-world scenario, this tool would:
    # 1. Perform spatial subtraction (Demand Density - Existing Capacity).
    # 2. Identify clusters of Tier 1 anchors located >20km from the nearest substation.
    # 3. Flag 'Agricultural Cold Spots' where lack of power prevents local processing.

    response = {
        "gaps_found": 3,
        "critical_gap": {
            "location": "Lome-Cotonou Border Zone",
            "unmet_demand_mw": 120.0,
            "opportunity_type": "Agro-Processing SEZ"
        },
        "message": "3 critical infrastructure gaps identified."
    }

    return Command(
        update={
            "messages": [
                ToolMessage(content=json.dumps(response), tool_call_id=runtime.tool_call_id)
            ]
        }
    )
