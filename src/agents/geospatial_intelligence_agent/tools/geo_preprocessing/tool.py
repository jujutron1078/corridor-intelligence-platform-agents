import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("geo_preprocessing", description=TOOL_DESCRIPTION)
def geo_preprocessing_tool( runtime: ToolRuntime) -> Command:
    """
    Mock tool: reproject, normalize, mosaic, tile imagery into inference-ready chips.
    """
    result = {
        "status": "ok",
        "step": "preprocessing",
        "chip_count": 128,
        "crs": "EPSG:3857",
        
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

