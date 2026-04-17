"""End-to-end tests — verifies the full stack from API to agents to tools.

These tests verify:
1. FastAPI app starts and serves all routes
2. Agent orchestrator loads with all sub-agents
3. Pipeline bridge connects tools to services
4. Chat service classifies and routes queries
5. Conversation state persists across messages
"""

import json

import pytest

# ── 1. FastAPI App ───────────────────────────────────────────────────────────

class TestFastAPIApp:
    @pytest.fixture(scope="class")
    def client(self):
        from fastapi.testclient import TestClient
        from src.api.main import app
        return TestClient(app)

    def test_root_returns_platform_info(self, client):
        r = client.get("/")
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "Corridor Intelligence Platform"
        assert data["version"] == "0.2.0"

    def test_health_ok(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert "model_routes" in data
        assert len(data["model_routes"]) == 6

    def test_liveness_probe(self, client):
        r = client.get("/api/healthz/live")
        assert r.status_code == 200
        assert r.json()["status"] == "alive"

    def test_readiness_probe(self, client):
        r = client.get("/api/healthz/ready")
        data = r.json()
        assert data["status"] in ("ready", "not_ready")
        assert "services" in data
        assert "database" in data

    def test_corridor_info(self, client):
        r = client.get("/api/corridor/info")
        assert r.status_code == 200
        data = r.json()
        assert len(data["nodes"]) == 13
        assert len(data["countries"]) == 5

    def test_corridor_layers(self, client):
        r = client.get("/api/corridor/layers")
        assert r.status_code == 200
        assert len(r.json()) == 17

    def test_usage_endpoint(self, client):
        r = client.get("/api/usage")
        assert r.status_code == 200
        data = r.json()
        assert "total_queries" in data
        assert "total_cost_usd" in data

    @pytest.mark.parametrize("path", [
        "/api/roads",
        "/api/infrastructure",
        "/api/minerals",
        "/api/economic-anchors",
        "/api/social",
        "/api/conflict",
        "/api/energy/plants",
        "/api/energy/grid",
        "/api/indicators/available",
    ])
    def test_data_endpoints_200(self, client, path):
        assert client.get(path).status_code == 200
# ── 2. Agent Orchestrator ────────────────────────────────────────────────────

class TestOrchestratorAgent:
    def test_orchestrator_loads(self):
        from src.agents.orchestrator_agent.agent import agent
        assert agent is not None
        assert type(agent).__name__ == "CompiledStateGraph"

    def test_all_6_subagents_registered(self):
        from src.agents.orchestrator_agent.sub_agent import (
            geospatial_intelligence_agent,
            opportunity_identification_agent,
            infrastructure_optimization_agent,
            economic_impact_modeling_agent,
            financing_optimization_agent,
            stakeholder_intelligence_agent,
        )
        # All should be importable without error
        assert geospatial_intelligence_agent is not None

    def test_all_6_domain_agents_load(self):
        agents = [
            "src.agents.geospatial_intelligence_agent.agent",
            "src.agents.opportunity_identification_agent.agent",
            "src.agents.infrastructure_optimization_agent.agent",
            "src.agents.economic_impact_modeling_agent.agent",
            "src.agents.financing_optimization_agent.agent",
            "src.agents.stakeholder_intelligence_agent.agent",
        ]
        import importlib
        for agent_path in agents:
            mod = importlib.import_module(agent_path)
            assert hasattr(mod, "agent"), f"{agent_path} missing 'agent' attribute"

    def test_37_tool_imports(self):
        """All 37 domain tools should import without error."""
        import importlib
        tool_paths = {
            "geospatial_intelligence_agent": [
                "geocode_location_tool", "define_corridor_tool", "fetch_geospatial_layers_tool",
                "terrain_analysis_tool", "environmental_constraints_tool",
                "infrastructure_detection_tool", "route_optimization_tool",
            ],
            "opportunity_identification_agent": [
                "scan_anchor_loads_tool", "calculate_current_demand_tool", "assess_bankability_tool",
                "model_growth_trajectory_tool", "economic_gap_analysis_tool", "prioritize_opportunities_tool",
            ],
            "infrastructure_optimization_agent": [
                "refine_optimized_routes_tool", "quantify_colocation_benefits_tool",
                "size_voltage_and_capacity_tool", "optimize_substation_placement_tool",
                "generate_phasing_strategy_tool", "generate_cost_estimates_tool",
            ],
            "economic_impact_modeling_agent": [
                "calculate_gdp_multipliers_tool", "model_employment_impact_tool",
                "assess_poverty_reduction_tool", "quantify_catalytic_effects_tool",
                "model_regional_integration_tool", "perform_impact_scenario_analysis_tool",
            ],
            "financing_optimization_agent": [
                "match_dfi_institutions_tool", "generate_financing_scenarios_tool",
                "build_financial_model_tool", "optimize_debt_terms_tool",
                "model_credit_enhancement_tool", "perform_risk_and_sensitivity_analysis_tool",
            ],
            "stakeholder_intelligence_agent": [
                "map_stakeholder_ecosystem_tool", "analyze_influence_networks_tool",
                "assess_stakeholder_risks_tool", "generate_engagement_roadmap_tool",
                "generate_tailored_messaging_tool", "track_engagement_sentiment_tool",
            ],
        }
        count = 0
        for agent_name, tools in tool_paths.items():
            for tool_name in tools:
                importlib.import_module(f"src.agents.{agent_name}.tools.{tool_name}.tool")
                count += 1
        assert count == 37
# ── 3. Pipeline Bridge Integration ──────────────────────────────────────────

class TestPipelineBridgeIntegration:
    def test_corridor_info_feeds_tools(self):
        """Verify corridor info is accessible to tools."""
        from src.adapters.pipeline_bridge import pipeline_bridge
        info = pipeline_bridge.get_corridor_info()
        assert info["status"] == "success"
        # Tools use these fields
        assert "countries" in info
        assert "nodes" in info
        assert "bbox" in info

    def test_infrastructure_detections_feed_tools(self):
        """Verify infrastructure detections are accessible (may be empty without data)."""
        from src.adapters.pipeline_bridge import pipeline_bridge
        result = pipeline_bridge.get_infrastructure_detections()
        assert "detections" in result
        assert "detection_count" in result
        assert result["detection_count"] == len(result["detections"])

    def test_conflict_data_flat_for_tools(self):
        """Verify conflict data uses the flat structure tools expect."""
        from src.adapters.pipeline_bridge import pipeline_bridge
        result = pipeline_bridge.get_conflict_data()
        # Phase 2 fix: tools access these at top level
        assert "total_events" in result
        assert "risk_level" in result
# ── 4. Chat Service ─────────────────────────────────────────────────────────

class TestChatServiceClassification:
    def test_classify_imports(self):
        from src.api.services.chat_service import classify_query
        assert callable(classify_query)

    def test_tools_available(self):
        from src.api.services.chat_service import DATA_TOOLS
        assert len(DATA_TOOLS) >= 25

    def test_system_prompt_comprehensive(self):
        from src.api.services.chat_service import CORRIDOR_SYSTEM_PROMPT
        # Should mention key data sources
        assert "nightlights" in CORRIDOR_SYSTEM_PROMPT.lower()
        assert "infrastructure" in CORRIDOR_SYSTEM_PROMPT.lower()
# ── 5. Conversation Persistence ─────────────────────────────────────────────

class TestConversationPersistence:
    def test_save_and_retrieve(self):
        from src.api.services.conversation_store import save_conversation, get_conversation
        conv_id = "e2e-test-conv"
        messages = [
            {"role": "user", "content": "What infrastructure is near Lagos?"},
            {"role": "assistant", "content": "Near Lagos, I found several ports..."},
        ]
        save_conversation(conv_id, messages)
        retrieved = get_conversation(conv_id)
        assert len(retrieved) == 2
        assert retrieved[0]["content"] == "What infrastructure is near Lagos?"

    def test_conversation_context_passed_to_agent(self):
        """Verify agent_bridge accepts conversation history."""
        import inspect
        from src.api.services.agent_bridge import invoke_agent
        sig = inspect.signature(invoke_agent)
        assert "conversation_history" in sig.parameters
# ── 6. LLM and Model Routing ────────────────────────────────────────────────

class TestLLMIntegration:
    def test_llm_selector_produces_model(self):
        from src.shared.agents.llm.llm_selector import make_llm
        llm = make_llm("gpt-4o", temperature=0.1)
        assert llm is not None

    def test_all_routes_have_valid_models(self):
        from src.api.config import MODEL_ROUTES
        from src.shared.agents.llm.llm_selector import make_llm
        for route_name, route in MODEL_ROUTES.items():
            llm = make_llm(route["model"], temperature=route["temperature"])
            assert llm is not None, f"Failed to create LLM for route '{route_name}'"
# ── 7. Full Stack Smoke Test ────────────────────────────────────────────────

class TestFullStackSmoke:
    """Smoke test that exercises the complete stack without calling LLMs."""

    @pytest.fixture(scope="class")
    def client(self):
        from fastapi.testclient import TestClient
        from src.api.main import app
        return TestClient(app)

    def test_health_to_data_flow(self, client):
        """Health → corridor → infrastructure chain."""
        health = client.get("/api/health").json()
        assert health["status"] == "ok"

        info = client.get("/api/corridor/info").json()
        assert len(info["nodes"]) == 13

        roads = client.get("/api/roads").json()
        assert roads["type"] == "FeatureCollection"

        minerals = client.get("/api/minerals").json()
        assert minerals["type"] == "FeatureCollection"

    def test_pipeline_bridge_to_tool_chain(self):
        """Pipeline bridge → tool execution chain."""
        from src.adapters.pipeline_bridge import pipeline_bridge
        from unittest.mock import MagicMock
        import json

        # 1. Get corridor info
        info = pipeline_bridge.get_corridor_info()
        assert len(info["countries"]) == 5

        # 2. Feed into stakeholder mapping
        from src.agents.stakeholder_intelligence_agent.tools.map_stakeholder_ecosystem_tool.tool import map_stakeholder_ecosystem_tool
        from src.agents.stakeholder_intelligence_agent.tools.map_stakeholder_ecosystem_tool.schema import StakeholderMappingInput

        rt = MagicMock()
        rt.tool_call_id = "smoke-test"
        payload = StakeholderMappingInput(
            corridor_countries=["Nigeria", "Ghana", "Togo"],
            project_scope="Lagos-Abidjan corridor power infrastructure",
        )
        result = map_stakeholder_ecosystem_tool.func(payload, rt)
        data = json.loads(result.update["messages"][0].content)
        assert data["total_identified"] > 0
        assert "NGA" in data["countries_analyzed"]
