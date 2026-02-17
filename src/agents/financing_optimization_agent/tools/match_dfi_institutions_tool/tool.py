import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import DFIMatchingInput


@tool("match_dfi_institutions", description=TOOL_DESCRIPTION)
def match_dfi_institutions_tool(
    payload: DFIMatchingInput, runtime: ToolRuntime
) -> Command:
    """Matches the project to potential DFI funders based on mandate and eligibility."""

    # In a real-world scenario, this tool would:
    # 1. Query a database of DFI investment mandates.
    # 2. Filter by country eligibility (e.g., IDA vs IBRD status).
    # 3. Rank institutions by their historical appetite for regional West African infrastructure.

    response = {
        "eligible_institutions": [
            {"name": "African Development Bank (AfDB)", "focus": "Regional Integration", "relevance": 0.98},
            {"name": "EU Global Gateway", "focus": "Green Energy/Digital", "relevance": 0.92},
            {"name": "IFC", "focus": "Private Sector Infrastructure", "relevance": 0.85}
        ],
        "engagement_sequence": ["Approach AfDB for anchor concessionality", "Engage EU for grants"],
        "message": "DFI matching complete. High alignment with AfDB Regional Integration mandate."
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
