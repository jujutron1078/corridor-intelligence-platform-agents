import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .schema import DefineCorridorInput
from .description import TOOL_DESCRIPTION

@tool("define_corridor", description=TOOL_DESCRIPTION)
def define_corridor_tool(
    payload: DefineCorridorInput, runtime: ToolRuntime
) -> Command:
    """
    Creates a geographic bounding polygon (corridor) between two points.
    It expands the center line by the buffer_width to include 'Left' (North) 
    and 'Right' (South) zones for comprehensive infrastructure analysis.
    """
    
    # 1. Geometry Specs
    # The Abidjan-Lagos route is ~1,080km. 
    # A 50km total buffer means 25km North and 25km South of the centerline.
    corridor_length = 1045.2 
    total_area = corridor_length * payload.buffer_width_km
    
    # 2. Mock GeoJSON Logic
    # We are traveling West to East. 
    # North (Left) is a higher Latitude (+). South (Right) is a lower Latitude (-).
    # We create a 4-point bounding box (plus a 5th point to close the loop).
    
    mock_geojson = {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                # Point 1: Top Left (North-West of Abidjan)
                # Moving ~0.25 degrees North (~25km) from Abidjan start
                [-4.008, 5.600], 

                # Point 2: Top Right (North-East of Lagos)
                # Moving ~0.25 degrees North (~25km) from Lagos end
                [3.379, 6.750],  

                # Point 3: Bottom Right (South-East of Lagos)
                # Moving ~0.25 degrees South (~25km) from Lagos end
                [3.379, 6.250],  

                # Point 4: Bottom Left (South-West of Abidjan)
                # Moving ~0.25 degrees South (~25km) from Abidjan start
                [-4.008, 5.100], 

                # Point 5: Close the Polygon (Return to Point 1)
                [-4.008, 5.600]  
            ]]
        },
        "properties": {
            "buffer_km": payload.buffer_width_km,
            "corridor_id": "AL_CORRIDOR_POC_001",
            "description": "Area covering coastal ports and inland agro-zones"
        }
    }

    # 3. Constructing the Agent Response
    # This data is passed to Tool 3 (Fetch Layers) to clip satellite imagery.
    response = {
        "corridor_id": "AL_CORRIDOR_POC_001",
        "length_km": corridor_length,
        "area_sqkm": total_area,
        "bounding_polygon_geojson": mock_geojson,
        "status": "success",
        "message": f"Corridor defined with {payload.buffer_width_km}km total width."
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