import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import EnvironmentalInput


@tool("environmental_constraints", description=TOOL_DESCRIPTION)
def environmental_constraints_tool(
    payload: EnvironmentalInput, runtime: ToolRuntime
) -> Command:
    """
    Identifies legal and environmental 'No-Go' zones by checking 
    overlap between the corridor and protected area databases.
    """
    
    # In a real-world scenario, this tool would:
    # 1. Load the vector data (GeoJSON/Shapefile) from Tool 3.
    # 2. Perform a 'Spatial Join' or 'Intersection' between the corridor and protected polygons.
    # 3. Apply a buffer (e.g., 500m) to all detected protected sites.
    # 4. Query the 'IUCN Red List' or local UNESCO records for cultural sites.

    response = {
        "status": "Environmental Audit Complete",
        "protected_areas_found": 2,
        "critical_conflicts": [
            {
                "name": "Omo Forest Reserve",
                "risk_level": "High",
                "reason": "Intercepts primary forest area (Strictly Prohibited)"
            }
        ],
        "mitigation_required": True,
        "message": "Corridor requires adjustments to comply with International Environmental Standards."
    }

    return Command(
        update={
            "messages": [
                ToolMessage(content=json.dumps(response), tool_call_id=runtime.tool_call_id)
            ]
        }
    )