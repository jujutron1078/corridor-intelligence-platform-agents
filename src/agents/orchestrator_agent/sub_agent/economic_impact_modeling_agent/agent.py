from langchain.tools import tool, ToolRuntime
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from src.agents.economic_impact_modeling_agent.agent import agent as econ_agent
from src.agents.orchestrator_agent.sub_agent._bridge import build_sub_agent_result


@tool(
    "economic_impact_modeling_agent",
    description=(
        "Model economic impact of investments: GDP multipliers, employment projections, "
        "poverty reduction, catalytic effects, and scenario comparisons. Use for: "
        "jobs analysis, GDP impact, economic modeling, development impact."
    ),
)
async def economic_impact_modeling_agent(
    task: str, runtime: ToolRuntime
) -> Command:
    response = await econ_agent.ainvoke({"messages": [HumanMessage(content=task)]})
    return build_sub_agent_result(response, runtime.tool_call_id)
