from langchain.agents import create_agent

from src.shared.llm.llm_selector import default_llm, dynamic_model_selector
from src.agents.stakeholder_intelligence_agent.context.context import Context
from src.agents.stakeholder_intelligence_agent.middleware.inject_context import inject_context
from src.agents.stakeholder_intelligence_agent.prompts.prompt import agent_prompt
from src.agents.stakeholder_intelligence_agent.state.state import StakeholderIntelligenceAgentState
from src.agents.stakeholder_intelligence_agent.tools import (
    map_stakeholder_ecosystem_tool,
    analyze_influence_networks_tool,
    generate_engagement_roadmap_tool,
    assess_stakeholder_risks_tool,
    generate_tailored_messaging_tool,
    track_engagement_sentiment_tool,
)
from src.shared.tools import think_tool, write_todos

agent = create_agent(
    model=default_llm,
    tools=[
        think_tool,
        write_todos,
        map_stakeholder_ecosystem_tool,
        analyze_influence_networks_tool,
        generate_engagement_roadmap_tool,
        assess_stakeholder_risks_tool,
        generate_tailored_messaging_tool,
        track_engagement_sentiment_tool,
    ],
    context_schema=Context,
    state_schema=StakeholderIntelligenceAgentState,
    middleware=[
        inject_context,
        agent_prompt,
        dynamic_model_selector,
    ],
)

