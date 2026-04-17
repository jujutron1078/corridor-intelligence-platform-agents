"""Smoke tests for agent modules and shared agent utilities."""

import sys
from pathlib import Path

import pytest

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestAgentImports:
    """Verify all 7 agents import without error."""

    def test_orchestrator_agent(self):
        __import__("src.agents.orchestrator_agent.agent")

    def test_geospatial_intelligence_agent(self):
        __import__("src.agents.geospatial_intelligence_agent.agent")

    def test_opportunity_identification_agent(self):
        __import__("src.agents.opportunity_identification_agent.agent")

    def test_infrastructure_optimization_agent(self):
        __import__("src.agents.infrastructure_optimization_agent.agent")

    def test_economic_impact_modeling_agent(self):
        __import__("src.agents.economic_impact_modeling_agent.agent")

    def test_financing_optimization_agent(self):
        __import__("src.agents.financing_optimization_agent.agent")

    def test_stakeholder_intelligence_agent(self):
        __import__("src.agents.stakeholder_intelligence_agent.agent")


class TestSharedAgentImports:
    """Verify shared agent utilities import."""

    def test_llm_selector(self):
        __import__("src.shared.agents.llm.llm_selector")

    def test_llm_models(self):
        __import__("src.shared.agents.llm.models")

    def test_think_tool(self):
        __import__("src.shared.agents.tools.think_tool")

    def test_todo_tool(self):
        __import__("src.shared.agents.tools.todo_tool")

    def test_company_info(self):
        __import__("src.shared.agents.utils.company_info")

    def test_get_today_str(self):
        __import__("src.shared.agents.utils.get_today_str")

    def test_progress(self):
        __import__("src.shared.agents.utils.progress")


class TestAgentToolImports:
    """Verify key agent tools import."""

    def test_fetch_geospatial_layers_tool(self):
        __import__("src.agents.geospatial_intelligence_agent.tools.fetch_geospatial_layers_tool.tool")

    def test_define_corridor_tool(self):
        __import__("src.agents.geospatial_intelligence_agent.tools.define_corridor_tool.tool")

    def test_terrain_analysis_tool(self):
        __import__("src.agents.geospatial_intelligence_agent.tools.terrain_analysis_tool.tool")

    def test_infrastructure_detection_tool(self):
        __import__("src.agents.geospatial_intelligence_agent.tools.infrastructure_detection_tool.tool")

    def test_geocode_location_tool(self):
        __import__("src.agents.geospatial_intelligence_agent.tools.geocode_location_tool.tool")

    def test_scan_anchor_loads_tool(self):
        __import__("src.agents.opportunity_identification_agent.tools.scan_anchor_loads_tool.tool")

    def test_calculate_current_demand_tool(self):
        __import__("src.agents.opportunity_identification_agent.tools.calculate_current_demand_tool.tool")

    def test_economic_gap_analysis_tool(self):
        __import__("src.agents.opportunity_identification_agent.tools.economic_gap_analysis_tool.tool")
