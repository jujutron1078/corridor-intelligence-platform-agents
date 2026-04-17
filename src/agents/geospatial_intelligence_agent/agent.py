from langchain.agents import create_agent

from src.shared.agents.llm.llm_selector import default_llm, dynamic_model_selector
from src.shared.agents.middleware.trim_context import trim_tool_messages
from src.agents.geospatial_intelligence_agent.context.context import Context
from src.agents.geospatial_intelligence_agent.middleware.inject_context import inject_context
from src.agents.geospatial_intelligence_agent.prompts.prompt import agent_prompt
from src.agents.geospatial_intelligence_agent.state.state import GeospatialIntelligenceAgentState
from src.shared.agents.tools import think_tool, write_todos
from src.agents.geospatial_intelligence_agent.tools.define_corridor_tool.tool import (
    define_corridor_tool,
)
from src.agents.geospatial_intelligence_agent.tools.environmental_constraints_tool.tool import (
    environmental_constraints_tool,
)
from src.agents.geospatial_intelligence_agent.tools.fetch_geospatial_layers_tool.tool import (
    fetch_geospatial_layers_tool,
)
from src.agents.geospatial_intelligence_agent.tools.geocode_location_tool.tool import (
    geocode_location_tool,
)
from src.agents.geospatial_intelligence_agent.tools.infrastructure_detection_tool.tool import (
    infrastructure_detection_tool,
)
from src.agents.geospatial_intelligence_agent.tools.route_optimization_tool.tool import (
    route_optimization_tool,
)
from src.agents.geospatial_intelligence_agent.tools.terrain_analysis_tool.tool import (
    terrain_analysis_tool,
)
from src.agents.geospatial_intelligence_agent.tools.climate_risk_tool.tool import (
    climate_risk_assessment,
)

agent = create_agent(
    model=default_llm,
    tools=[
        think_tool,
        write_todos,
        geocode_location_tool,
        define_corridor_tool,
        fetch_geospatial_layers_tool,
        terrain_analysis_tool,
        infrastructure_detection_tool,
        environmental_constraints_tool,
        route_optimization_tool,
        climate_risk_assessment,
    ],
    context_schema=Context,
    state_schema=GeospatialIntelligenceAgentState,
    middleware=[
        inject_context,
        trim_tool_messages,
        agent_prompt,
        dynamic_model_selector,
    ],
)
