from langchain.tools import tool, ToolRuntime
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from src.agents.geospatial_intelligence_agent.agent import agent as geo_agent
from src.agents.orchestrator_agent.sub_agent._bridge import build_sub_agent_result


@tool(
    "geospatial_intelligence_agent",
    description=(
        "Geospatial analysis: route optimization, terrain analysis, satellite imagery, "
        "environmental constraints, and infrastructure detection (ports, roads, power "
        "plants, transmission lines). Use for: route planning, mapping, corridor "
        "definition, spatial analysis, nightlights, elevation, land cover."
    ),
)
async def geospatial_intelligence_agent(
    task: str, runtime: ToolRuntime
) -> Command:
    response = await geo_agent.ainvoke({"messages": [HumanMessage(content=task)]})
    return build_sub_agent_result(response, runtime.tool_call_id)
