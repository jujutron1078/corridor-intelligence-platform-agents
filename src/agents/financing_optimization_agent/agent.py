from langchain.agents import create_agent

from src.shared.agents.llm.llm_selector import default_llm, dynamic_model_selector
from src.shared.agents.middleware.trim_context import trim_tool_messages
from src.agents.financing_optimization_agent.context.context import Context
from src.agents.financing_optimization_agent.middleware.inject_context import inject_context
from src.agents.financing_optimization_agent.prompts.prompt import agent_prompt
from src.agents.financing_optimization_agent.state.state import FinancingOptimizationAgentState
from src.agents.financing_optimization_agent.tools import (
    match_dfi_institutions_tool,
    generate_financing_scenarios_tool,
    build_financial_model_tool,
    perform_risk_and_sensitivity_analysis_tool,
    optimize_debt_terms_tool,
    model_credit_enhancement_tool,
)
from src.shared.agents.tools import think_tool, write_todos

agent = create_agent(
    model=default_llm,
    tools=[
        think_tool,
        write_todos,
        match_dfi_institutions_tool,
        generate_financing_scenarios_tool,
        build_financial_model_tool,
        perform_risk_and_sensitivity_analysis_tool,
        optimize_debt_terms_tool,
        model_credit_enhancement_tool,
    ],
    context_schema=Context,
    state_schema=FinancingOptimizationAgentState,
    middleware=[
        inject_context,
        trim_tool_messages,
        agent_prompt,
        dynamic_model_selector,
    ],
)

