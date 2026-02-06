from langchain.agents import create_agent

from src.shared.llm.llm_selector import default_llm, dynamic_model_selector
from src.agents.infrastructure_optimization_agent.context.context import Context
from src.agents.infrastructure_optimization_agent.middleware.inject_context import inject_context
from src.agents.infrastructure_optimization_agent.prompts.prompt import agent_prompt
from src.agents.infrastructure_optimization_agent.state.state import InfrastructureOptimizationAgentState
from src.agents.infrastructure_optimization_agent.tools import (
    infra_input_validator_tool,
    infra_cost_surface_tool,
    infra_route_optimization_tool,
    infra_colocation_quant_tool,
    infra_substation_siting_tool,
    infra_phasing_optimizer_tool,
    infra_costing_engine_tool,
    infra_tech_spec_generator_tool,
    infra_output_packager_tool,
)
from src.shared.tools import think_tool, write_todos

agent = create_agent(
    model=default_llm,
    tools=[
        think_tool,
        write_todos,
        infra_input_validator_tool,
        infra_cost_surface_tool,
        infra_route_optimization_tool,
        infra_colocation_quant_tool,
        infra_substation_siting_tool,
        infra_phasing_optimizer_tool,
        infra_costing_engine_tool,
        infra_tech_spec_generator_tool,
        infra_output_packager_tool,
    ],
    context_schema=Context,
    state_schema=InfrastructureOptimizationAgentState,
    middleware=[
        inject_context,
        agent_prompt,
        dynamic_model_selector,
    ],
)

