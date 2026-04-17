from langchain.agents import create_agent

from src.agents.orchestrator_agent.context.context import Context
from src.agents.orchestrator_agent.middleware.inject_context import inject_context
from src.agents.orchestrator_agent.prompts.prompt import agent_prompt
from src.agents.orchestrator_agent.state.state import OrchestratorAgentState

from src.shared.agents.llm.llm_selector import default_llm, dynamic_model_selector
from src.shared.agents.middleware.trim_context import trim_tool_messages
from src.shared.agents.tools import think_tool, write_todos
from src.shared.agents.tools.corridor_data_tool import query_corridor_data
from src.shared.agents.checkpoint import get_checkpointer
from src.agents.orchestrator_agent.sub_agent import (
    geospatial_intelligence_agent,
    opportunity_identification_agent,
    infrastructure_optimization_agent,
    economic_impact_modeling_agent,
    financing_optimization_agent,
    stakeholder_intelligence_agent,
)

_checkpointer = get_checkpointer()

agent = create_agent(
    model=default_llm,
    tools=[
        # Shared meta-tools
        think_tool,
        write_todos,
        # Direct data access — query ANY corridor data without routing to sub-agents
        query_corridor_data,
        # High-level agent tools (for complex multi-step analysis)
        geospatial_intelligence_agent,
        opportunity_identification_agent,
        infrastructure_optimization_agent,
        economic_impact_modeling_agent,
        financing_optimization_agent,
        stakeholder_intelligence_agent,
    ],
    context_schema=Context,
    state_schema=OrchestratorAgentState,
    middleware=[
        inject_context,
        trim_tool_messages,
        agent_prompt,
        dynamic_model_selector,
    ],
    checkpointer=_checkpointer,
)

