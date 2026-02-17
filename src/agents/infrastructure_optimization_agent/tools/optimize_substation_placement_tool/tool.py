import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import SubstationPlacementInput


@tool("optimize_substation_placement", description=TOOL_DESCRIPTION)
def optimize_substation_placement_tool(
    payload: SubstationPlacementInput, runtime: ToolRuntime
) -> Command:
    """Determines optimal GPS locations for substations based on load proximity."""

    # In a real-world scenario, this tool would:
    # 1. Use 'K-means clustering' to find centers of gravity for anchor loads.
    # 2. Ensure substations are placed within 10km of major industrial clusters.
    # 3. Check for flat terrain and road access for the substation footprint.

    response = {
        "recommended_substations": [
            {
                "id": "SUB_ABIDJAN_EAST",
                "coords": [5.36, -3.94],
                "serves": ["Azito", "Industrial_Zone_A"],
            },
            {
                "id": "SUB_TARKWA_HUB",
                "coords": [5.30, -2.00],
                "serves": ["Gold_Mine_A", "Gold_Mine_B"],
            },
        ],
        "total_substations": 8,
        "message": "Substation locations optimized for maximum anchor load connectivity.",
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
