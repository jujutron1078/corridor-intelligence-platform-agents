from langchain.agents import create_agent

from src.shared.llm.llm_selector import default_llm, dynamic_model_selector
from src.agents.opportunity_identification_agent.context.context import Context
from src.agents.opportunity_identification_agent.middleware.inject_context import inject_context
from src.agents.opportunity_identification_agent.prompts.prompt import agent_prompt
from src.agents.opportunity_identification_agent.state.state import OpportunityIdentificationAgentState
from src.shared.tools import think_tool, write_todos
from src.agents.opportunity_identification_agent.tools.scan_anchor_loads_tool.tool import (
    scan_anchor_loads_tool,
)
from src.agents.opportunity_identification_agent.tools.calculate_current_demand_tool.tool import (
    calculate_current_demand_tool,
)
from src.agents.opportunity_identification_agent.tools.assess_bankability_tool.tool import (
    assess_bankability_tool,
)
from src.agents.opportunity_identification_agent.tools.model_growth_trajectory_tool.tool import (
    model_growth_trajectory_tool,
)
from src.agents.opportunity_identification_agent.tools.economic_gap_analysis_tool.tool import (
    economic_gap_analysis_tool,
)
from src.agents.opportunity_identification_agent.tools.prioritize_opportunities_tool.tool import (
    prioritize_opportunities_tool,
)

agent = create_agent(
    model=default_llm,
    tools=[
        think_tool,
        write_todos,
        scan_anchor_loads_tool,
        calculate_current_demand_tool,
        assess_bankability_tool,
        model_growth_trajectory_tool,
        economic_gap_analysis_tool,
        prioritize_opportunities_tool,
    ],
    context_schema=Context,
    state_schema=OpportunityIdentificationAgentState,
    middleware=[
        inject_context,
        agent_prompt,
        dynamic_model_selector,
    ],
)

