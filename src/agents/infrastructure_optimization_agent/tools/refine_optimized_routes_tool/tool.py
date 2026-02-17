import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import RouteRefinementInput


@tool("refine_optimized_routes", description=TOOL_DESCRIPTION)
def refine_optimized_routes_tool(
    payload: RouteRefinementInput, runtime: ToolRuntime
) -> Command:
    """Refines route variants to maximize corridor alignment and minimize cost."""

    # In a real-world scenario, this tool would:
    # 1. Snap the power line route to the highway centerline where possible.
    # 2. Adjust for 'Turning Radius' and engineering tolerances for pylons.
    # 3. Optimize for 'Crossings' (e.g., crossing the highway or rivers).

    response = {
        "status": "Route Refinement Complete",
        "refined_variants": [
            {"id": "V1_CORRIDOR", "total_length_km": 1082.5, "alignment_score": 0.94}
        ],
        "message": "Routes adjusted to stay within the 500m corridor proximity limit.",
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
