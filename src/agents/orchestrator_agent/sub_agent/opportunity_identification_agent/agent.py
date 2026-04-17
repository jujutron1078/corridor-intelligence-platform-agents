from langchain.tools import tool, ToolRuntime
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from src.agents.opportunity_identification_agent.agent import agent as opp_agent
from src.agents.orchestrator_agent.sub_agent._bridge import build_sub_agent_result


@tool(
    "opportunity_identification_agent",
    description=(
        "Identify investment opportunities along the corridor. Scans FAO agriculture "
        "production data, trade value chains, OSM infrastructure, and minerals to find "
        "processing gaps, underserved zones, and bankable opportunities. Returns concrete "
        "opportunities with production volumes, investment estimates, annual returns, "
        "employment impact, and bankability scores. Use for: agriculture opportunities, "
        "trade opportunities, investment analysis, processing gaps, value chains, "
        "where to invest, crop analysis, economic opportunities."
    ),
)
async def opportunity_identification_agent(
    task: str, runtime: ToolRuntime
) -> Command:
    response = await opp_agent.ainvoke({"messages": [HumanMessage(content=task)]})
    return build_sub_agent_result(response, runtime.tool_call_id)
