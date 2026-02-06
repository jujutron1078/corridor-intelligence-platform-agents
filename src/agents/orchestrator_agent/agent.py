from langchain.agents import create_agent

from src.agents.orchestrator_agent.context.context import Context
from src.agents.orchestrator_agent.middleware.inject_context import inject_context
from src.agents.orchestrator_agent.prompts.prompt import agent_prompt
from src.agents.orchestrator_agent.state.state import OrchestratorAgentState

from src.shared.llm.llm_selector import default_llm, dynamic_model_selector
from src.shared.tools import think_tool, write_todos
from src.agents.orchestrator_agent.sub_agent import (
    geospatial_intelligence_agent,
    opportunity_identification_agent,
    infrastructure_optimization_agent,
    economic_impact_modeling_agent,
    financing_optimization_agent,
    stakeholder_intelligence_agent,
    realtime_monitoring_agent,
)


agent = create_agent(
    model=default_llm,
    tools=[
        # Shared meta-tools
        think_tool,
        write_todos,
        # High-level agent tools
        geospatial_intelligence_agent,
        opportunity_identification_agent,
        infrastructure_optimization_agent,
        economic_impact_modeling_agent,
        financing_optimization_agent,
        stakeholder_intelligence_agent,
        realtime_monitoring_agent,
    ],
    context_schema=Context,
    state_schema=OrchestratorAgentState,
    middleware=[
        inject_context,
        agent_prompt,
        dynamic_model_selector,
    ],
)

