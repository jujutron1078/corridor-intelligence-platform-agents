from langchain.agents import create_agent

from src.shared.llm.llm_selector import default_llm, dynamic_model_selector
from src.agents.opportunity_identification_agent.context.context import Context
from src.agents.opportunity_identification_agent.middleware.inject_context import inject_context
from src.agents.opportunity_identification_agent.prompts.prompt import agent_prompt
from src.agents.opportunity_identification_agent.state.state import OpportunityIdentificationAgentState
from src.agents.opportunity_identification_agent.tools import (
    opp_input_validator_tool,
    opp_source_ingestion_tool,
    opp_entity_resolution_tool,
    opp_demand_estimation_tool,
    opp_growth_projection_tool,
    opp_bankability_scorer_tool,
    opp_portfolio_builder_tool,
    opp_output_packager_tool,
)
from src.shared.tools import think_tool, write_todos

agent = create_agent(
    model=default_llm,
    tools=[
        think_tool,
        write_todos,
        opp_input_validator_tool,
        opp_source_ingestion_tool,
        opp_entity_resolution_tool,
        opp_demand_estimation_tool,
        opp_growth_projection_tool,
        opp_bankability_scorer_tool,
        opp_portfolio_builder_tool,
        opp_output_packager_tool,
    ],
    context_schema=Context,
    state_schema=OpportunityIdentificationAgentState,
    middleware=[
        inject_context,
        agent_prompt,
        dynamic_model_selector,
    ],
)

