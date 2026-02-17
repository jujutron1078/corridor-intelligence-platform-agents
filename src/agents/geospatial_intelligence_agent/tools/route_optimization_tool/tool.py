import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import RouteOptimizationInput


@tool("route_optimization", description=TOOL_DESCRIPTION)
def route_optimization_tool(
    payload: RouteOptimizationInput, runtime: ToolRuntime
) -> Command:
    """
    Calculates the most efficient infrastructure paths by combining
    terrain, environmental, and infrastructure data.
    """

    # In a real-world scenario, this tool would:
    # 1. Create a 'Weighted Cost Grid' where pixels in protected areas = Infinite Cost.
    # 2. Use A* or Dijkstra's algorithm to find the lowest-accumulated-cost path.
    # 3. Smooth the line to ensure it meets engineering 'Turning Radius' standards.
    # 4. Calculate the 'Co-location %' by checking proximity to existing transport layers.

    response = {
        "status": "Optimization Complete",
        "variants_generated": 50,
        "optimized_routes": [
            {
                "variant_id": "ALT_ROUTE_01",
                "total_length_km": 1088.4,
                "estimated_capex_usd": "2.1B",
                "terrain_difficulty": "Low",
                "co_location_index": 0.85,
                "geometry_geojson": '{"type":"LineString","coordinates":[[...]]}'
            },
            {
                "variant_id": "ALT_ROUTE_02",
                "total_length_km": 1052.1,
                "estimated_capex_usd": "2.8B",
                "terrain_difficulty": "High",
                "co_location_index": 0.12,
                "geometry_geojson": '{"type":"LineString","coordinates":[[...]]}'
            }
        ],
        "best_option": {
            "id": "AL_OPTIMIZED_V1",
            "length_km": 1082.5,
            "savings_vs_baseline": "22%",
            "environmental_impact": "Minimal (Avoids Omo Forest)"
        },
        "recommendation": "ALT_ROUTE_01 offers 15% CAPEX savings due to highway co-location.",
        "geospatial_file": "s3://atlantis/results/optimized_routes.kml",
        "message": "Routes generated. Final report ready for stakeholder review."
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
