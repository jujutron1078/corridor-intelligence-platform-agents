from langchain.agents import create_agent

from src.shared.agents.llm.llm_selector import default_llm, dynamic_model_selector
from src.shared.agents.middleware.trim_context import trim_tool_messages
from src.agents.infrastructure_optimization_agent.context.context import Context
from src.agents.infrastructure_optimization_agent.middleware.inject_context import inject_context
from src.agents.infrastructure_optimization_agent.prompts.prompt import agent_prompt
from src.agents.infrastructure_optimization_agent.state.state import InfrastructureOptimizationAgentState
from src.shared.agents.tools import think_tool, write_todos
from src.agents.infrastructure_optimization_agent.tools import (
    refine_optimized_routes_tool,
    quantify_colocation_benefits_tool,
    size_voltage_and_capacity_tool,
    optimize_substation_placement_tool,
    generate_phasing_strategy_tool,
    generate_cost_estimates_tool,
)

agent = create_agent(
    model=default_llm,
    tools=[
        think_tool,
        write_todos,
        refine_optimized_routes_tool,
        quantify_colocation_benefits_tool,
        size_voltage_and_capacity_tool,
        optimize_substation_placement_tool,
        generate_phasing_strategy_tool,
        generate_cost_estimates_tool,
    ],
    context_schema=Context,
    state_schema=InfrastructureOptimizationAgentState,
    middleware=[
        inject_context,
        trim_tool_messages,
        agent_prompt,
        dynamic_model_selector,
    ],
)

