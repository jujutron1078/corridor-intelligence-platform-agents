import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import CapacitySizingInput


@tool("size_voltage_and_capacity", description=TOOL_DESCRIPTION)
def size_voltage_and_capacity_tool(
    payload: CapacitySizingInput, runtime: ToolRuntime
) -> Command:
    """Determines optimal voltage, conductor type, and capacity for the line."""

    # In a real-world scenario, this tool would:
    # 1. Calculate Surge Impedance Loading (SIL).
    # 2. Compare 330kV vs 400kV for line losses over 1000km+.
    # 3. Recommend conductor bundles (e.g., Quad-bundle ACSR).

    response = {
        "technical_specs": {
            "recommended_voltage": "400 kV",
            "conductor_type": "Quad-bundle ACSR",
            "max_capacity_mw": 3200,
            "estimated_line_losses": "3.2%",
        },
        "message": "Optimal voltage and capacity sizing complete for long-distance transmission.",
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
