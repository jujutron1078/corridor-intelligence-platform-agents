from langchain.agents import create_agent

from src.shared.llm.llm_selector import default_llm, dynamic_model_selector
from src.agents.financing_optimization_agent.context.context import Context
from src.agents.financing_optimization_agent.middleware.inject_context import inject_context
from src.agents.financing_optimization_agent.prompts.prompt import agent_prompt
from src.agents.financing_optimization_agent.state.state import FinancingOptimizationAgentState
from src.agents.financing_optimization_agent.tools import (
    fin_input_validator_tool,
    fin_base_model_tool,
    fin_scenario_generator_tool,
    fin_optimizer_tool,
    fin_monte_carlo_risk_tool,
    fin_term_sheet_synthesizer_tool,
    fin_output_packager_tool,
)
from src.shared.tools import think_tool, write_todos

agent = create_agent(
    model=default_llm,
    tools=[
        think_tool,
        write_todos,
        fin_input_validator_tool,
        fin_base_model_tool,
        fin_scenario_generator_tool,
        fin_optimizer_tool,
        fin_monte_carlo_risk_tool,
        fin_term_sheet_synthesizer_tool,
        fin_output_packager_tool,
    ],
    context_schema=Context,
    state_schema=FinancingOptimizationAgentState,
    middleware=[
        inject_context,
        agent_prompt,
        dynamic_model_selector,
    ],
)

