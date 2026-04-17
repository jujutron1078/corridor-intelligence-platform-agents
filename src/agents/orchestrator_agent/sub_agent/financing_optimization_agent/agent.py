from langchain.tools import tool, ToolRuntime
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from src.agents.financing_optimization_agent.agent import agent as fin_agent
from src.agents.orchestrator_agent.sub_agent._bridge import build_sub_agent_result


@tool(
    "financing_optimization_agent",
    description=(
        "Design financing structures: blended finance scenarios, DFI matching, "
        "IRR/DSCR analysis, credit enhancement, and debt optimization. Use for: "
        "funding strategy, investor matching, financial modeling."
    ),
)
async def financing_optimization_agent(
    task: str, runtime: ToolRuntime
) -> Command:
    response = await fin_agent.ainvoke({"messages": [HumanMessage(content=task)]})
    return build_sub_agent_result(response, runtime.tool_call_id)
