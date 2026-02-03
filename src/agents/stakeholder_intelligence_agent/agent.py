from langchain.agents import create_agent

from src.shared.llm.llm_selector import default_llm, dynamic_model_selector
from src.agents.stakeholder_intelligence_agent.context.context import Context
from src.agents.stakeholder_intelligence_agent.middleware.inject_context import inject_context
from src.agents.stakeholder_intelligence_agent.prompts.prompt import agent_prompt
from src.agents.stakeholder_intelligence_agent.state.state import StakeholderIntelligenceAgentState
from src.agents.stakeholder_intelligence_agent.tools import (
    stake_input_validator_tool,
    stake_harvesting_tool,
    stake_entity_resolution_tool,
    stake_influence_graph_tool,
    stake_engagement_planner_tool,
    stake_risk_register_tool,
    stake_output_packager_tool,
)
from src.shared.tools import think_tool, write_todos

agent = create_agent(
    model=default_llm,
    tools=[
        think_tool,
        write_todos,
        stake_input_validator_tool,
        stake_harvesting_tool,
        stake_entity_resolution_tool,
        stake_influence_graph_tool,
        stake_engagement_planner_tool,
        stake_risk_register_tool,
        stake_output_packager_tool,
    ],
    context_schema=Context,
    state_schema=StakeholderIntelligenceAgentState,
    middleware=[
        inject_context,
        agent_prompt,
        dynamic_model_selector,
    ],
)

