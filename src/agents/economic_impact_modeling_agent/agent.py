from langchain.agents import create_agent

from src.shared.llm.llm_selector import default_llm, dynamic_model_selector
from src.agents.economic_impact_modeling_agent.context.context import Context
from src.agents.economic_impact_modeling_agent.middleware.inject_context import inject_context
from src.agents.economic_impact_modeling_agent.prompts.prompt import agent_prompt
from src.agents.economic_impact_modeling_agent.state.state import EconomicImpactModelingAgentState
from src.shared.tools import think_tool, write_todos

agent = create_agent(
    model=default_llm,
    tools=[
        think_tool,
        write_todos,
    ],
    context_schema=Context,
    state_schema=EconomicImpactModelingAgentState,
    middleware=[
        inject_context,
        agent_prompt,
        dynamic_model_selector
    ],
)
