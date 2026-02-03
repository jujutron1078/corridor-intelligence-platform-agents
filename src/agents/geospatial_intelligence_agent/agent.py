from langchain.agents import create_agent

from src.shared.llm.llm_selector import default_llm, dynamic_model_selector
from src.agents.geospatial_intelligence_agent.context.context import Context
from src.agents.geospatial_intelligence_agent.middleware.inject_context import inject_context
from src.agents.geospatial_intelligence_agent.prompts.prompt import agent_prompt
from src.agents.geospatial_intelligence_agent.state.state import GeospatialIntelligenceAgentState
from src.agents.geospatial_intelligence_agent.tools import (
    geo_input_validation_tool,
    geo_data_catalog_tool,
    geo_imagery_acquisition_tool,
    geo_preprocessing_tool,
    geo_cv_inference_tool,
    geo_postprocess_tool,
    geo_terrain_constraints_tool,
    geo_route_generator_tool,
    geo_colocation_analyzer_tool,
    geo_output_packager_tool,
    geo_qa_benchmark_tool,
)
from src.shared.tools import think_tool, write_todos

agent = create_agent(
    model=default_llm,
    tools=[
        think_tool,
        write_todos,
        geo_input_validation_tool,
        geo_data_catalog_tool,
        geo_imagery_acquisition_tool,
        geo_preprocessing_tool,
        geo_cv_inference_tool,
        geo_postprocess_tool,
        geo_terrain_constraints_tool,
        geo_route_generator_tool,
        geo_colocation_analyzer_tool,
        geo_output_packager_tool,
        geo_qa_benchmark_tool,
    ],
    context_schema=Context,
    state_schema=GeospatialIntelligenceAgentState,
    middleware=[
        inject_context,
        agent_prompt,
        dynamic_model_selector,
    ],
)

