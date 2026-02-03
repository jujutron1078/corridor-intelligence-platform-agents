from langchain.agents import create_agent

from src.shared.llm.llm_selector import default_llm, dynamic_model_selector
from src.agents.realtime_monitoring_agent.context.context import Context
from src.agents.realtime_monitoring_agent.middleware.inject_context import inject_context
from src.agents.realtime_monitoring_agent.prompts.prompt import agent_prompt
from src.agents.realtime_monitoring_agent.state.state import RealtimeMonitoringAgentState
from src.agents.realtime_monitoring_agent.tools import (
    rt_baseline_validator_tool,
    rt_live_feed_ingestor_tool,
    rt_satellite_monitoring_tool,
    rt_kpi_calculator_tool,
    rt_early_warning_engine_tool,
    rt_recommendation_engine_tool,
    rt_report_generator_tool,
)
from src.shared.tools import think_tool, write_todos

agent = create_agent(
    model=default_llm,
    tools=[
        think_tool,
        write_todos,
        rt_baseline_validator_tool,
        rt_live_feed_ingestor_tool,
        rt_satellite_monitoring_tool,
        rt_kpi_calculator_tool,
        rt_early_warning_engine_tool,
        rt_recommendation_engine_tool,
        rt_report_generator_tool,
    ],
    context_schema=Context,
    state_schema=RealtimeMonitoringAgentState,
    middleware=[
        inject_context,
        agent_prompt,
        dynamic_model_selector,
    ],
)

