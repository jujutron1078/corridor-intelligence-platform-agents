"""Tests to verify tool outputs are compatible with the frontend parser.

The frontend's map-overlay.ts expects specific field names and structures
in tool output JSON. These tests ensure our tools produce compatible output.
"""

import json
from unittest.mock import MagicMock

import pytest

def make_runtime():
    rt = MagicMock()
    rt.tool_call_id = "compat-test"
    return rt
def extract_response(command) -> dict:
    return json.loads(command.update["messages"][0].content)
class TestRouteOptimizationOutput:
    """Frontend expects route_variants array with coordinate data."""

    def test_has_route_variants_key(self):
        from src.agents.geospatial_intelligence_agent.tools.route_optimization_tool.tool import route_optimization_tool
        from src.agents.geospatial_intelligence_agent.tools.route_optimization_tool.schema import RouteOptimizationInput
        payload = RouteOptimizationInput(priority="balance")
        result = route_optimization_tool.func(payload, make_runtime())
        data = extract_response(result)
        # Should have either route_variants (graph available) or route_analysis (fallback)
        has_variants = "route_variants" in data
        has_fallback = "route_analysis" in data
        assert has_variants or has_fallback

    def test_route_variants_structure(self):
        """If route_variants exists, verify frontend-compatible structure."""
        from src.agents.geospatial_intelligence_agent.tools.route_optimization_tool.tool import route_optimization_tool
        from src.agents.geospatial_intelligence_agent.tools.route_optimization_tool.schema import RouteOptimizationInput
        payload = RouteOptimizationInput(priority="balance")
        result = route_optimization_tool.func(payload, make_runtime())
        data = extract_response(result)
        if "route_variants" in data:
            variants = data["route_variants"]
            assert isinstance(variants, list)
            assert len(variants) >= 1
            v = variants[0]
            # Frontend parseRouteVariants expects these fields
            assert "coordinates" in v or "route_geojson" in v
            assert "label" in v or "variant_name" in v or "name" in v
            if "distance_km" in v:
                assert isinstance(v["distance_km"], (int, float))
class TestInfrastructureDetectionOutput:
    """Frontend expects detections array with specific coordinate format."""

    def test_detections_structure(self):
        from src.agents.geospatial_intelligence_agent.tools.infrastructure_detection_tool.tool import infrastructure_detection_tool
        from src.agents.geospatial_intelligence_agent.tools.infrastructure_detection_tool.schema import DetectionInput
        payload = DetectionInput(satellite_image_uri="sentinel-2-test", types=["substation", "port_facility"])
        result = infrastructure_detection_tool.func(payload, make_runtime())
        data = extract_response(result)
        assert "detections" in data
        for det in data["detections"][:3]:
            assert "type" in det
            assert "detection_id" in det or "name" in det
class TestStakeholderToolOutputs:
    """Verify stakeholder tools include expected fields."""

    def test_risk_assessment_has_register(self):
        from src.agents.stakeholder_intelligence_agent.tools.assess_stakeholder_risks_tool.tool import assess_stakeholder_risks_tool
        from src.agents.stakeholder_intelligence_agent.tools.assess_stakeholder_risks_tool.schema import StakeholderRiskInput
        payload = StakeholderRiskInput(stakeholder_profiles=[
            {"name": "Nigeria FGN", "type": "government", "influence": "high"},
        ])
        result = assess_stakeholder_risks_tool.func(payload, make_runtime())
        data = extract_response(result)
        assert "risk_register" in data
        for risk in data["risk_register"]:
            assert "category" in risk
            assert "risk" in risk
            assert "level" in risk
            assert "mitigation" in risk

    def test_sentiment_scores_all_categories(self):
        from src.agents.stakeholder_intelligence_agent.tools.track_engagement_sentiment_tool.tool import (
            track_engagement_sentiment_tool, BASELINE_SENTIMENT,
        )
        from src.agents.stakeholder_intelligence_agent.tools.track_engagement_sentiment_tool.schema import SentimentTrackingInput
        payload = SentimentTrackingInput(stakeholder_ids=["stkh-001"])
        result = track_engagement_sentiment_tool.func(payload, make_runtime())
        data = extract_response(result)
        scores = data["sentiment_scores"]
        for category in BASELINE_SENTIMENT:
            assert category in scores
            assert 0 <= scores[category] <= 1

    def test_ecosystem_mapping_counts(self):
        from src.agents.stakeholder_intelligence_agent.tools.map_stakeholder_ecosystem_tool.tool import map_stakeholder_ecosystem_tool
        from src.agents.stakeholder_intelligence_agent.tools.map_stakeholder_ecosystem_tool.schema import StakeholderMappingInput
        payload = StakeholderMappingInput(
            corridor_countries=["Nigeria", "Ghana"],
            project_scope="Lagos-Abidjan corridor power infrastructure",
        )
        result = map_stakeholder_ecosystem_tool.func(payload, make_runtime())
        data = extract_response(result)
        counts = data["stakeholder_counts"]
        assert "governments" in counts
        assert "dfis" in counts
        assert "regional_bodies" in counts
        assert data["total_identified"] == sum(counts.values())
class TestFinancingToolOutputs:
    """Verify financing tool output structure."""

    def test_bankability_tiers(self):
        from src.agents.opportunity_identification_agent.tools.assess_bankability_tool.tool import assess_bankability_tool
        from src.agents.opportunity_identification_agent.tools.assess_bankability_tool.schema import BankabilityInput
        payload = BankabilityInput(anchor_load_ids=["anchor-001", "anchor-002"])
        result = assess_bankability_tool.func(payload, make_runtime())
        data = extract_response(result)
        if data.get("bankability_scores"):
            for score in data["bankability_scores"][:3]:
                assert "score" in score
                assert "tier" in score
                assert score["tier"] in ("Tier 1", "Tier 2", "Tier 3")
                assert 0 <= score["score"] <= 1

    def test_prioritized_opportunities_ranked(self):
        from src.agents.opportunity_identification_agent.tools.prioritize_opportunities_tool.tool import prioritize_opportunities_tool
        result = prioritize_opportunities_tool.func({}, make_runtime())
        data = extract_response(result)
        plist = data.get("priority_list", [])
        if len(plist) >= 2:
            # Should be sorted by composite_score descending
            scores = [p["composite_score"] for p in plist]
            assert scores == sorted(scores, reverse=True)
            # Should have ranks
            assert plist[0]["rank"] == 1
class TestAllToolsHaveMessage:
    """Every tool output should include a 'message' field for the frontend."""

    TOOL_MODULES = [
        ("src.agents.geospatial_intelligence_agent.tools.define_corridor_tool.tool", "define_corridor_tool", "DefineCorridorInput"),
        ("src.agents.geospatial_intelligence_agent.tools.route_optimization_tool.tool", "route_optimization_tool", "RouteOptimizationInput"),
        ("src.agents.stakeholder_intelligence_agent.tools.assess_stakeholder_risks_tool.tool", "assess_stakeholder_risks_tool", "StakeholderRiskInput"),
        ("src.agents.stakeholder_intelligence_agent.tools.track_engagement_sentiment_tool.tool", "track_engagement_sentiment_tool", "SentimentTrackingInput"),
    ]

    @pytest.mark.parametrize("module_path,tool_name,schema_name", TOOL_MODULES)
    def test_message_field_exists(self, module_path, tool_name, schema_name):
        import importlib
        mod = importlib.import_module(module_path)
        tool_fn = getattr(mod, tool_name)

        # Try to import and instantiate the schema with required fields
        # Replace only the last ".tool" segment with ".schema"
        schema_module = module_path.rsplit(".tool", 1)[0] + ".schema"
        try:
            schema_mod = importlib.import_module(schema_module)
            schema_cls = getattr(schema_mod, schema_name)
            if schema_name == "StakeholderMappingInput":
                payload = schema_cls(corridor_countries=["Nigeria"], project_scope="test")
            elif schema_name == "MessagingInput":
                payload = schema_cls(stakeholder_type="government", key_interests=["jobs"])
            elif schema_name == "DefineCorridorInput":
                payload = schema_cls(
                    source={"latitude": 6.45, "longitude": 3.40},
                    destination={"latitude": 5.36, "longitude": -3.97},
                    buffer_width_km=50.0,
                )
            elif schema_name == "RouteOptimizationInput":
                payload = schema_cls(priority="balance")
            elif schema_name == "StakeholderRiskInput":
                payload = schema_cls(stakeholder_profiles=[{"name": "Test", "type": "gov"}])
            elif schema_name == "SentimentTrackingInput":
                payload = schema_cls(stakeholder_ids=["stkh-001"])
            else:
                payload = schema_cls()
        except Exception:
            payload = {}

        result = tool_fn.func(payload, make_runtime())
        data = extract_response(result)
        assert "message" in data, f"{tool_name} output missing 'message' field"
