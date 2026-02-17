import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import DetectionInput


@tool("infrastructure_detection", description=TOOL_DESCRIPTION)
def infrastructure_detection_tool(
    payload: DetectionInput, runtime: ToolRuntime
) -> Command:
    """
    Runs computer vision inference on satellite imagery to detect
    anchor loads and existing infrastructure points.
    """
    # In a real-world scenario, this tool would:
    # 1. Load a pre-trained CV model (e.g., YOLOv8 or Segment Anything Model)
    # 2. Slice the high-resolution satellite mosaic (from Tool 3) into smaller tiles
    # 3. Perform inference to detect bounding boxes for factories, ports, and plants
    # 4. Georeference the pixel coordinates back to Latitude/Longitude

    # Mocking the CV model detection results
    response = {
        "detections": [
            {
                "type": "industrial_complex",
                "coords": [5.312, -3.980],
                "confidence": 0.94,
                "is_new_construction": True,  # AI detected this isn't on old maps
                "estimated_power_demand_mw": 15.5,
            },
            {
                "type": "substation",
                "coords": [5.380, -3.920],
                "confidence": 0.72,  # Low confidence - might be a warehouse
                "action_required": "manual_verification",
            },
        ],
        "summary": "Detected 12 anchor loads. 3 are newly identified since the 2023 census.",
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
