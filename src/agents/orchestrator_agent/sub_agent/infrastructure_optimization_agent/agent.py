from langchain.tools import tool, ToolRuntime
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from src.agents.infrastructure_optimization_agent.agent import agent as infra_agent
from src.agents.orchestrator_agent.sub_agent._bridge import build_sub_agent_result


@tool(
    "infrastructure_optimization_agent",
    description=(
        "Optimize infrastructure design: route selection, CAPEX/OPEX estimation, "
        "capacity sizing, phasing strategy, and cost-benefit analysis. Use for: "
        "infrastructure costs, technical design, construction phasing."
    ),
)
async def infrastructure_optimization_agent(
    task: str, runtime: ToolRuntime
) -> Command:
    response = await infra_agent.ainvoke({"messages": [HumanMessage(content=task)]})
    return build_sub_agent_result(response, runtime.tool_call_id)
