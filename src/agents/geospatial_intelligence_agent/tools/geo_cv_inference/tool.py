import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("geo_cv_inference", description=TOOL_DESCRIPTION)
def geo_cv_inference_tool(config: dict, runtime: ToolRuntime) -> Command:
    """
    Mock tool: run CV inference and detect infrastructure assets.
    """
    result = {
        "status": "ok",
        "step": "cv_inference",
        "detections": [
            {"id": "plant_001", "type": "power_plant", "confidence": 0.93},
            {"id": "port_001", "type": "port", "confidence": 0.9},
            {"id": "substation_001", "type": "substation", "confidence": 0.88},
        ],
        "echo": config,
    }
    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=json.dumps(result),
                    tool_call_id=runtime.tool_call_id,
                )
            ]
        }
    )

