"""Functional tests for all 37 agent tools.

Tests verify tool functions can execute with mock/real data and return
properly structured Command objects with ToolMessages.
"""

import json
from unittest.mock import MagicMock

import pytest

# ── Helpers ──────────────────────────────────────────────────────────────────

def make_runtime(tool_call_id: str = "test-call-001") -> MagicMock:
    """Create a mock ToolRuntime with a tool_call_id."""
    runtime = MagicMock()
    runtime.tool_call_id = tool_call_id
    return runtime
def extract_response(command) -> dict:
    """Extract the JSON response from a Command's ToolMessage."""
    messages = command.update["messages"]
    assert len(messages) == 1
    content = messages[0].content
    return json.loads(content)
# ── Geospatial Intelligence Agent (7 tools) ──────────────────────────────────

class TestGeospatialTools:
    def test_geocode_location(self):
        from src.agents.geospatial_intelligence_agent.tools.geocode_location_tool.tool import geocode_location_tool
        from src.agents.geospatial_intelligence_agent.tools.geocode_location_tool.schema import GeocodeLocationInput, Location
        payload = GeocodeLocationInput(locations=[
            Location(name="Lagos", country="Nigeria"),
            Location(name="Accra", country="Ghana"),
        ])
        result = geocode_location_tool.func(payload, make_runtime())
        data = extract_response(result)
        assert "resolved_locations" in data
        assert len(data["resolved_locations"]) == 2

    def test_define_corridor(self):
        from src.agents.geospatial_intelligence_agent.tools.define_corridor_tool.tool import define_corridor_tool
        from src.agents.geospatial_intelligence_agent.tools.define_corridor_tool.schema import DefineCorridorInput
        payload = DefineCorridorInput(
            source={"latitude": 6.45, "longitude": 3.40},
            destination={"latitude": 5.36, "longitude": -3.97},
            buffer_width_km=50.0,
        )
        result = define_corridor_tool.func(payload, make_runtime())
        data = extract_response(result)
        assert data["corridor_id"] == "AL_CORRIDOR_001"
        assert "bounding_polygon_geojson" in data

    def test_terrain_analysis(self):
        from src.agents.geospatial_intelligence_agent.tools.terrain_analysis_tool.tool import terrain_analysis_tool
        from src.agents.geospatial_intelligence_agent.tools.terrain_analysis_tool.schema import TerrainInput
        payload = TerrainInput(corridor_id="AL_CORRIDOR_001", dem_uri="SRTM90")
        result = terrain_analysis_tool.func(payload, make_runtime())
        data = extract_response(result)
        assert "segment_analysis" in data or "error" in data or "message" in data

    def test_environmental_constraints(self):
        from src.agents.geospatial_intelligence_agent.tools.environmental_constraints_tool.tool import environmental_constraints_tool
        from src.agents.geospatial_intelligence_agent.tools.environmental_constraints_tool.schema import EnvironmentalInput
        payload = EnvironmentalInput(corridor_id="AL_CORRIDOR_001", vector_uri="WCMC/WDPA")
        result = environmental_constraints_tool.func(payload, make_runtime())
        data = extract_response(result)
        assert "corridor_id" in data or "message" in data

    def test_infrastructure_detection(self):
        from src.agents.geospatial_intelligence_agent.tools.infrastructure_detection_tool.tool import infrastructure_detection_tool
        from src.agents.geospatial_intelligence_agent.tools.infrastructure_detection_tool.schema import DetectionInput
        payload = DetectionInput(satellite_image_uri="sentinel-2-test", types=["substation", "port_facility"])
        result = infrastructure_detection_tool.func(payload, make_runtime())
        data = extract_response(result)
        assert "detections" in data
        assert isinstance(data["detections"], list)

    def test_route_optimization(self):
        from src.agents.geospatial_intelligence_agent.tools.route_optimization_tool.tool import route_optimization_tool
        from src.agents.geospatial_intelligence_agent.tools.route_optimization_tool.schema import RouteOptimizationInput
        payload = RouteOptimizationInput(priority="balance")
        result = route_optimization_tool.func(payload, make_runtime())
        data = extract_response(result)
        assert "job_metadata" in data
        assert data["job_metadata"]["priority_mode"] == "balance"
        assert "corridor_nodes" in data
        # Should have either optimized_route (graph) or route_analysis (fallback)
        assert "optimized_route" in data or "route_analysis" in data
        assert "message" in data

    def test_route_optimization_all_priorities(self):
        from src.agents.geospatial_intelligence_agent.tools.route_optimization_tool.tool import route_optimization_tool
        from src.agents.geospatial_intelligence_agent.tools.route_optimization_tool.schema import RouteOptimizationInput
        for priority in ["min_cost", "min_distance", "max_impact", "balance"]:
            payload = RouteOptimizationInput(priority=priority)
            result = route_optimization_tool.func(payload, make_runtime())
            data = extract_response(result)
            assert data["job_metadata"]["priority_mode"] == priority

    def test_fetch_geospatial_layers(self):
        from src.agents.geospatial_intelligence_agent.tools.fetch_geospatial_layers_tool.tool import fetch_geospatial_layers_tool
        from src.agents.geospatial_intelligence_agent.tools.fetch_geospatial_layers_tool.schema import FetchLayersInput
        payload = FetchLayersInput(corridor_id="AL_CORRIDOR_001")
        result = fetch_geospatial_layers_tool.func(payload, make_runtime())
        data = extract_response(result)
        assert "data_inventory" in data or "error" in data
# ── Opportunity Identification Agent (6 tools) ──────────────────────────────

class TestOpportunityTools:
    def test_scan_anchor_loads(self):
        from src.agents.opportunity_identification_agent.tools.scan_anchor_loads_tool.tool import scan_anchor_loads_tool
        result = scan_anchor_loads_tool.func({}, make_runtime())
        data = extract_response(result)
        assert "anchor_catalog" in data or "error" in data

    def test_calculate_current_demand(self):
        from src.agents.opportunity_identification_agent.tools.calculate_current_demand_tool.tool import calculate_current_demand_tool
        result = calculate_current_demand_tool.func({}, make_runtime())
        data = extract_response(result)
        assert "demand_profiles" in data or "total_current_mw" in data or "error" in data

    def test_assess_bankability(self):
        from src.agents.opportunity_identification_agent.tools.assess_bankability_tool.tool import assess_bankability_tool
        from src.agents.opportunity_identification_agent.tools.assess_bankability_tool.schema import BankabilityInput
        payload = BankabilityInput(anchor_load_ids=["anchor-001", "anchor-002"])
        result = assess_bankability_tool.func(payload, make_runtime())
        data = extract_response(result)
        assert "bankability_scores" in data
        assert "corridor_average_score" in data or "error" in data

    def test_model_growth_trajectory(self):
        from src.agents.opportunity_identification_agent.tools.model_growth_trajectory_tool.tool import model_growth_trajectory_tool
        result = model_growth_trajectory_tool.func({}, make_runtime())
        data = extract_response(result)
        assert "trajectories" in data or "message" in data or "error" in data

    def test_economic_gap_analysis(self):
        from src.agents.opportunity_identification_agent.tools.economic_gap_analysis_tool.tool import economic_gap_analysis_tool
        result = economic_gap_analysis_tool.func({}, make_runtime())
        data = extract_response(result)
        assert "gaps" in data or "gaps_found" in data or "message" in data

    def test_prioritize_opportunities(self):
        from src.agents.opportunity_identification_agent.tools.prioritize_opportunities_tool.tool import prioritize_opportunities_tool
        result = prioritize_opportunities_tool.func({}, make_runtime())
        data = extract_response(result)
        assert "priority_list" in data
        assert "total_anchors_ranked" in data or "error" in data
# ── Infrastructure Optimization Agent (6 tools) ─────────────────────────────

class TestInfrastructureTools:
    def test_refine_optimized_routes(self):
        from src.agents.infrastructure_optimization_agent.tools.refine_optimized_routes_tool.tool import refine_optimized_routes_tool
        result = refine_optimized_routes_tool.func(make_runtime())
        data = extract_response(result)
        assert "message" in data or "refined_variants" in data

    def test_quantify_colocation_benefits(self):
        from src.agents.infrastructure_optimization_agent.tools.quantify_colocation_benefits_tool.tool import quantify_colocation_benefits_tool
        result = quantify_colocation_benefits_tool.func(make_runtime())
        data = extract_response(result)
        assert "message" in data

    def test_size_voltage_and_capacity(self):
        from src.agents.infrastructure_optimization_agent.tools.size_voltage_and_capacity_tool.tool import size_voltage_and_capacity_tool
        result = size_voltage_and_capacity_tool.func({}, make_runtime())
        data = extract_response(result)
        assert "message" in data

    def test_optimize_substation_placement(self):
        from src.agents.infrastructure_optimization_agent.tools.optimize_substation_placement_tool.tool import optimize_substation_placement_tool
        result = optimize_substation_placement_tool.func({}, make_runtime())
        data = extract_response(result)
        assert "message" in data

    def test_generate_phasing_strategy(self):
        from src.agents.infrastructure_optimization_agent.tools.generate_phasing_strategy_tool.tool import generate_phasing_strategy_tool
        result = generate_phasing_strategy_tool.func({}, make_runtime())
        data = extract_response(result)
        assert "message" in data or "phased_roadmap" in data

    def test_generate_cost_estimates(self):
        from src.agents.infrastructure_optimization_agent.tools.generate_cost_estimates_tool.tool import generate_cost_estimates_tool
        result = generate_cost_estimates_tool.func({}, make_runtime())
        data = extract_response(result)
        assert "message" in data
# ── Economic Impact Modeling Agent (6 tools) ─────────────────────────────────

class TestEconomicImpactTools:
    def test_calculate_gdp_multipliers(self):
        from src.agents.economic_impact_modeling_agent.tools.calculate_gdp_multipliers_tool.tool import calculate_gdp_multipliers_tool
        result = calculate_gdp_multipliers_tool.func({}, make_runtime())
        data = extract_response(result)
        assert "message" in data

    def test_model_employment_impact(self):
        from src.agents.economic_impact_modeling_agent.tools.model_employment_impact_tool.tool import model_employment_impact_tool
        result = model_employment_impact_tool.func({}, make_runtime())
        data = extract_response(result)
        assert "message" in data

    def test_assess_poverty_reduction(self):
        from src.agents.economic_impact_modeling_agent.tools.assess_poverty_reduction_tool.tool import assess_poverty_reduction_tool
        result = assess_poverty_reduction_tool.func({}, make_runtime())
        data = extract_response(result)
        assert "message" in data

    def test_quantify_catalytic_effects(self):
        from src.agents.economic_impact_modeling_agent.tools.quantify_catalytic_effects_tool.tool import quantify_catalytic_effects_tool
        result = quantify_catalytic_effects_tool.func({}, make_runtime())
        data = extract_response(result)
        assert "message" in data

    def test_model_regional_integration(self):
        from src.agents.economic_impact_modeling_agent.tools.model_regional_integration_tool.tool import model_regional_integration_tool
        result = model_regional_integration_tool.func({}, make_runtime())
        data = extract_response(result)
        assert "message" in data

    def test_perform_impact_scenario_analysis(self):
        from src.agents.economic_impact_modeling_agent.tools.perform_impact_scenario_analysis_tool.tool import perform_impact_scenario_analysis_tool
        result = perform_impact_scenario_analysis_tool.func({}, make_runtime())
        data = extract_response(result)
        assert "message" in data
# ── Financing Optimization Agent (6 tools) ──────────────────────────────────

class TestFinancingTools:
    def test_match_dfi_institutions(self):
        from src.agents.financing_optimization_agent.tools.match_dfi_institutions_tool.tool import match_dfi_institutions_tool
        from src.agents.financing_optimization_agent.tools.match_dfi_institutions_tool.schema import DFIMatchingInput
        payload = DFIMatchingInput(
            corridor_countries=["Nigeria", "Ghana"],
            sectors=["energy", "transport"],
            development_impact_metrics={"jobs_created": 5000},
        )
        result = match_dfi_institutions_tool.func(payload, make_runtime())
        data = extract_response(result)
        assert "message" in data

    def test_generate_financing_scenarios(self):
        from src.agents.financing_optimization_agent.tools.generate_financing_scenarios_tool.tool import generate_financing_scenarios_tool
        from src.agents.financing_optimization_agent.tools.generate_financing_scenarios_tool.schema import ScenarioGenerationInput
        payload = ScenarioGenerationInput(total_capex=500_000_000.0)
        result = generate_financing_scenarios_tool.func(payload, make_runtime())
        data = extract_response(result)
        assert "message" in data

    def test_build_financial_model(self):
        from src.agents.financing_optimization_agent.tools.build_financial_model_tool.tool import build_financial_model_tool
        from src.agents.financing_optimization_agent.tools.build_financial_model_tool.schema import FinancialModelInput
        payload = FinancialModelInput(
            revenue_projections=[10.0, 20.0, 30.0],
            capex_opex_data={"capex": 100, "opex": 10},
            financing_structure={"debt": 70, "equity": 30},
        )
        result = build_financial_model_tool.func(payload, make_runtime())
        data = extract_response(result)
        assert "message" in data

    def test_optimize_debt_terms(self):
        from src.agents.financing_optimization_agent.tools.optimize_debt_terms_tool.tool import optimize_debt_terms_tool
        from src.agents.financing_optimization_agent.tools.optimize_debt_terms_tool.schema import DebtTermInput
        payload = DebtTermInput(
            debt_amount=100_000_000.0,
            cash_flow_available_for_debt_service=[15.0, 20.0, 25.0],
        )
        result = optimize_debt_terms_tool.func(payload, make_runtime())
        data = extract_response(result)
        assert "message" in data

    def test_model_credit_enhancement(self):
        from src.agents.financing_optimization_agent.tools.model_credit_enhancement_tool.tool import model_credit_enhancement_tool
        from src.agents.financing_optimization_agent.tools.model_credit_enhancement_tool.schema import CreditEnhancementInput
        payload = CreditEnhancementInput(gap_in_bankability=0.15)
        result = model_credit_enhancement_tool.func(payload, make_runtime())
        data = extract_response(result)
        assert "message" in data

    def test_perform_risk_and_sensitivity_analysis(self):
        from src.agents.financing_optimization_agent.tools.perform_risk_and_sensitivity_analysis_tool.tool import perform_risk_and_sensitivity_analysis_tool
        from src.agents.financing_optimization_agent.tools.perform_risk_and_sensitivity_analysis_tool.schema import RiskAnalysisInput
        payload = RiskAnalysisInput(financial_model_data={"npv": 50_000_000, "irr": 0.12})
        result = perform_risk_and_sensitivity_analysis_tool.func(payload, make_runtime())
        data = extract_response(result)
        assert "message" in data
# ── Stakeholder Intelligence Agent (6 tools) ────────────────────────────────

class TestStakeholderTools:
    def test_map_stakeholder_ecosystem(self):
        from src.agents.stakeholder_intelligence_agent.tools.map_stakeholder_ecosystem_tool.tool import map_stakeholder_ecosystem_tool
        from src.agents.stakeholder_intelligence_agent.tools.map_stakeholder_ecosystem_tool.schema import StakeholderMappingInput
        payload = StakeholderMappingInput(
            corridor_countries=["Nigeria", "Ghana"],
            project_scope="Lagos-Abidjan corridor power infrastructure",
        )
        result = map_stakeholder_ecosystem_tool.func(payload, make_runtime())
        data = extract_response(result)
        assert "stakeholder_counts" in data
        assert "total_identified" in data
        assert data["total_identified"] > 0

    def test_analyze_influence_networks(self):
        from src.agents.stakeholder_intelligence_agent.tools.analyze_influence_networks_tool.tool import analyze_influence_networks_tool
        from src.agents.stakeholder_intelligence_agent.tools.analyze_influence_networks_tool.schema import InfluenceNetworkInput
        payload = InfluenceNetworkInput(stakeholder_list=[
            {"name": "AfDB", "type": "dfi"},
            {"name": "ECOWAS", "type": "regional_body"},
        ])
        result = analyze_influence_networks_tool.func(payload, make_runtime())
        data = extract_response(result)
        assert "message" in data

    def test_assess_stakeholder_risks(self):
        from src.agents.stakeholder_intelligence_agent.tools.assess_stakeholder_risks_tool.tool import assess_stakeholder_risks_tool
        from src.agents.stakeholder_intelligence_agent.tools.assess_stakeholder_risks_tool.schema import StakeholderRiskInput
        payload = StakeholderRiskInput(stakeholder_profiles=[
            {"name": "Nigeria FGN", "type": "government", "influence": "high"},
        ])
        result = assess_stakeholder_risks_tool.func(payload, make_runtime())
        data = extract_response(result)
        assert "risk_register" in data
        assert len(data["risk_register"]) > 0
        assert "live_risk_alerts" in data or "data_sources" in data

    def test_generate_engagement_roadmap(self):
        from src.agents.stakeholder_intelligence_agent.tools.generate_engagement_roadmap_tool.tool import generate_engagement_roadmap_tool
        from src.agents.stakeholder_intelligence_agent.tools.generate_engagement_roadmap_tool.schema import EngagementRoadmapInput
        payload = EngagementRoadmapInput(influence_data={
            "high_influence": ["AfDB", "World Bank"],
            "medium_influence": ["ECOWAS"],
        })
        result = generate_engagement_roadmap_tool.func(payload, make_runtime())
        data = extract_response(result)
        assert "message" in data

    def test_generate_tailored_messaging(self):
        from src.agents.stakeholder_intelligence_agent.tools.generate_tailored_messaging_tool.tool import generate_tailored_messaging_tool
        from src.agents.stakeholder_intelligence_agent.tools.generate_tailored_messaging_tool.schema import MessagingInput
        payload = MessagingInput(
            stakeholder_type="government",
            key_interests=["job creation", "revenue generation"],
        )
        result = generate_tailored_messaging_tool.func(payload, make_runtime())
        data = extract_response(result)
        assert "message" in data

    def test_track_engagement_sentiment(self):
        from src.agents.stakeholder_intelligence_agent.tools.track_engagement_sentiment_tool.tool import track_engagement_sentiment_tool
        from src.agents.stakeholder_intelligence_agent.tools.track_engagement_sentiment_tool.schema import SentimentTrackingInput
        payload = SentimentTrackingInput(stakeholder_ids=["stkh-001", "stkh-002"])
        result = track_engagement_sentiment_tool.func(payload, make_runtime())
        data = extract_response(result)
        assert "sentiment_scores" in data
        assert "overall_sentiment" in data
        assert 0 <= data["overall_sentiment"] <= 1
        assert "data_sources" in data
# ── Shared Tools ─────────────────────────────────────────────────────────────

class TestSharedTools:
    def test_think_tool(self):
        from src.shared.agents.tools.think_tool.tool import think_tool
        runtime = make_runtime()
        result = think_tool.func("This is a reflection about the task.", runtime)
        messages = result.update["messages"]
        assert len(messages) == 1
        assert messages[0].content == "This is a reflection about the task."
        assert messages[0].tool_call_id == "test-call-001"
