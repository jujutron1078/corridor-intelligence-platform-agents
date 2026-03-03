from langchain.agents import create_agent

from src.shared.llm.llm_selector import default_llm, dynamic_model_selector
from src.agents.economic_impact_modeling_agent.context.context import Context
from src.agents.economic_impact_modeling_agent.middleware.inject_context import inject_context
from src.agents.economic_impact_modeling_agent.prompts.prompt import agent_prompt
from src.agents.economic_impact_modeling_agent.state.state import EconomicImpactModelingAgentState
from src.shared.tools import think_tool, write_todos
from src.agents.economic_impact_modeling_agent.tools import (
    calculate_gdp_multipliers_tool,
    model_employment_impact_tool,
    assess_poverty_reduction_tool,
    quantify_catalytic_effects_tool,
    model_regional_integration_tool,
    perform_impact_scenario_analysis_tool,
)

agent = create_agent(
    model=default_llm,
    tools=[
        think_tool,
        write_todos,
        calculate_gdp_multipliers_tool,
        model_employment_impact_tool,
        assess_poverty_reduction_tool,
        quantify_catalytic_effects_tool,
        model_regional_integration_tool,
        perform_impact_scenario_analysis_tool,
    ],
    context_schema=Context,
    state_schema=EconomicImpactModelingAgentState,
    middleware=[
        inject_context,
        agent_prompt,
        dynamic_model_selector,
    ],
)

