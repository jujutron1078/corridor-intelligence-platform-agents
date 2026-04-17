from langchain.tools import tool, ToolRuntime
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from src.agents.stakeholder_intelligence_agent.agent import agent as stake_agent
from src.agents.orchestrator_agent.sub_agent._bridge import build_sub_agent_result


@tool(
    "stakeholder_intelligence_agent",
    description=(
        "Map stakeholders, influence networks, engagement plans, and risk registers. "
        "Use for: stakeholder analysis, political risk, community engagement, "
        "government relations."
    ),
)
async def stakeholder_intelligence_agent(
    task: str, runtime: ToolRuntime
) -> Command:
    response = await stake_agent.ainvoke({"messages": [HumanMessage(content=task)]})
    return build_sub_agent_result(response, runtime.tool_call_id)
