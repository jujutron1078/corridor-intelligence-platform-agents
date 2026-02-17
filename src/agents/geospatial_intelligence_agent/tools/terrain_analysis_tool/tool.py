import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import TerrainInput


@tool("terrain_analysis", description=TOOL_DESCRIPTION)
def terrain_analysis_tool(
    payload: TerrainInput, runtime: ToolRuntime
) -> Command:
    """
    Analyzes elevation data to calculate slopes, flood risks,
    and construction difficulty scores along the corridor.
    """

    # In a real-world scenario, this tool would:
    # 1. Access the Digital Elevation Model (DEM) clipped in Tool 3
    # 2. Run a 'Slope' algorithm to calculate the gradient between every pixel
    # 3. Generate a 'Cost Surface' (a map where steeper = more expensive)
    # 4. Identify drainage basins to predict flood-prone 'No-Go' zones

    response = {
        "segment_analysis": [
            {
                "start_km": 0, "end_km": 50,
                "avg_slope": 1.2,
                "soil_stability": "High",
                "flood_risk": "Low"
            },
            {
                "start_km": 50, "end_km": 85,
                "avg_slope": 6.8, # Warning: This increases costs by ~15%
                "soil_stability": "Medium (Sandy Clay)",
                "flood_risk": "Critical (Marshland detected)"
            }
        ],
        "total_excavation_estimate_m3": 1250000,
        "engineering_recommendation": "Avoid Segment 2; shift 3km North to bypass marshland."
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
