import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import GrowthTrajectoryInput


@tool("model_growth_trajectory", description=TOOL_DESCRIPTION)
def model_growth_trajectory_tool(
    payload: GrowthTrajectoryInput, runtime: ToolRuntime
) -> Command:
    """Projects future demand trajectories for the corridor anchors."""

    # In a real-world scenario, this tool would:
    # 1. Use time-series forecasting (e.g., Prophet) to model load growth.
    # 2. Incorporate Special Economic Zone (SEZ) masterplans to identify 'Step Loads'.
    # 3. Correlate growth with planned trade corridor logistics improvements.

    response = {
        "projection_summary": "Aggregated demand expected to grow by 240% over 20 years.",
        "trajectories": [
            {
                "anchor_id": "AL_ANC_042",
                "year_5_mw": 65.0,
                "year_20_mw": 110.0,
                "cagr": "5.2%"
            }
        ],
        "message": "20-year demand trajectories modeled."
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
