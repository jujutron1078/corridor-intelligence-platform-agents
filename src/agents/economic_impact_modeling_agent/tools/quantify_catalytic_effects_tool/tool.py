import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import CatalyticEffectsInput


@tool("quantify_catalytic_effects", description=TOOL_DESCRIPTION)
def quantify_catalytic_effects_tool(
    payload: CatalyticEffectsInput, runtime: ToolRuntime
) -> Command:
    """Calculates sector-specific growth unlocked by infrastructure."""

    # In a real-world scenario, this tool would:
    # 1. Calculate energy-cost savings for processing plants (e.g., Cocoa in Ghana).
    # 2. Model the increase in mining output enabled by reliable bulk power.
    # 3. Estimate 'Digital Economy' growth from fiber-optic co-location on power lines.

    response = {
        "sector_unlock_value_usd": {
            "agriculture_agro_processing": "1.2B",
            "mining_minerals": "2.4B",
            "manufacturing": "0.9B",
        },
        "digital_economy_impact": "High (Fiber-optic backbone included)",
        "message": "Sector-specific catalytic effects quantified.",
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
