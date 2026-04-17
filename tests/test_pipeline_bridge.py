"""Tests for the pipeline bridge adapter — all 28 methods."""
import pytest

class TestCorridorMethods:
    """Pipeline bridge: corridor info, define, geocode."""

    def test_get_corridor_info(self):
        from src.adapters.pipeline_bridge import pipeline_bridge
        info = pipeline_bridge.get_corridor_info()
        assert info["status"] == "success"
        assert info["corridor_id"] == "AL_CORRIDOR_001"
        assert len(info["countries"]) == 5
        assert len(info["nodes"]) == 13
        assert info["length_km"] == 1080
        assert info["buffer_km"] == 50
        assert info["geojson"]["type"] == "Feature"
        assert info["nodes_geojson"]["type"] == "FeatureCollection"
        assert "bbox" in info

    def test_define_corridor_default(self):
        from src.adapters.pipeline_bridge import pipeline_bridge
        result = pipeline_bridge.define_corridor()
        assert result["status"] == "success"
        assert result["corridor_id"] == "AL_CORRIDOR_001"
        assert result["bounding_polygon_geojson"]["type"] == "Feature"

    def test_define_corridor_custom_buffer(self):
        from src.adapters.pipeline_bridge import pipeline_bridge
        result = pipeline_bridge.define_corridor(buffer_width_km=100)
        assert result["area_sqkm"] == 1080 * 100

    def test_geocode_known_cities(self):
        from src.adapters.pipeline_bridge import pipeline_bridge
        result = pipeline_bridge.geocode_location(["Lagos", "Accra", "Abidjan"])
        locs = result["resolved_locations"]
        assert len(locs) == 3
        for loc in locs:
            assert loc["confidence"] == 0.98
            assert loc["latitude"] is not None
            assert loc["longitude"] is not None
            assert loc["source"] == "corridor_nodes"

    def test_geocode_partial_match(self):
        from src.adapters.pipeline_bridge import pipeline_bridge
        result = pipeline_bridge.geocode_location(["Tema"])
        assert result["resolved_locations"][0]["confidence"] == 0.98

    def test_geocode_unknown(self):
        from src.adapters.pipeline_bridge import pipeline_bridge
        result = pipeline_bridge.geocode_location(["NonexistentCity"])
        loc = result["resolved_locations"][0]
        assert loc["confidence"] == 0.0
        assert loc["source"] == "not_found"

    def test_geocode_empty_list(self):
        from src.adapters.pipeline_bridge import pipeline_bridge
        result = pipeline_bridge.geocode_location([])
        assert result["resolved_locations"] == []
class TestDataServiceMethods:
    """Pipeline bridge: data service methods (may return empty without data)."""

    def test_get_infrastructure_detections_structure(self):
        from src.adapters.pipeline_bridge import pipeline_bridge
        result = pipeline_bridge.get_infrastructure_detections()
        assert result["corridor_id"] == "AL_CORRIDOR_001"
        assert "detection_count" in result
        assert isinstance(result["detections"], list)

    def test_get_conflict_data_flat_structure(self):
        from src.adapters.pipeline_bridge import pipeline_bridge
        result = pipeline_bridge.get_conflict_data()
        # Verify the flat structure (Phase 2 fix)
        assert "total_events" in result
        assert "total_fatalities" in result
        assert "by_event_type" in result
        assert "by_country" in result
        assert "events" in result
        assert "risk_level" in result
        assert result["source"] == "ACLED"
        assert result["risk_level"] in ("low", "medium", "high", "critical")

    def test_get_conflict_data_risk_levels(self):
        from src.adapters.pipeline_bridge import pipeline_bridge
        result = pipeline_bridge.get_conflict_data()
        events = result["total_events"]
        level = result["risk_level"]
        if events > 500:
            assert level == "critical"
        elif events > 200:
            assert level == "high"
        elif events > 50:
            assert level == "medium"
        else:
            assert level == "low"

    def test_get_economic_anchors_structure(self):
        from src.adapters.pipeline_bridge import pipeline_bridge
        result = pipeline_bridge.get_economic_anchors()
        assert result["corridor_id"] == "AL_CORRIDOR_001"
        assert result["source"] == "USGS Mineral Resources"

    def test_get_worldbank_indicators_structure(self):
        from src.adapters.pipeline_bridge import pipeline_bridge
        result = pipeline_bridge.get_worldbank_indicators()
        assert result["corridor_id"] == "AL_CORRIDOR_001"
        assert result["source"] == "World Bank"
class TestNewPhase3Methods:
    """Pipeline bridge: Phase 3 additions."""

    def test_search_corridor_news_no_key(self, monkeypatch):
        """Without API key, should return unavailable status."""
        monkeypatch.setattr("src.api.config.TAVILY_API_KEY", "")
        # Force reimport
        from src.adapters import pipeline_bridge as pb_module
        import importlib
        importlib.reload(pb_module)
        result = pb_module.pipeline_bridge.search_corridor_news("test")
        assert result["status"] == "unavailable"
        assert result["results"] == []

    def test_search_corridor_news_default_query(self):
        from src.adapters.pipeline_bridge import pipeline_bridge
        result = pipeline_bridge.search_corridor_news()
        # Should work regardless of key availability
        assert "status" in result
        assert "results" in result
        assert isinstance(result["results"], list)

    def test_search_corridor_news_custom_query(self):
        from src.adapters.pipeline_bridge import pipeline_bridge
        result = pipeline_bridge.search_corridor_news("Ghana port investment", max_results=2)
        assert "query" in result
        assert "Ghana" in result["query"]

    def test_get_road_network_graph_returns_graph_or_none(self):
        from src.adapters.pipeline_bridge import pipeline_bridge
        result = pipeline_bridge.get_road_network_graph()
        if result is not None:
            import networkx as nx
            assert isinstance(result, nx.Graph)
            assert result.number_of_nodes() > 0

    def test_get_road_network_stats(self):
        from src.adapters.pipeline_bridge import pipeline_bridge
        result = pipeline_bridge.get_road_network_stats()
        assert isinstance(result, dict)


class TestEnrichedPipelineMethods:
    """Pipeline bridge: enriched data source methods (Phase 4)."""

    def test_get_imf_indicators(self):
        from src.adapters.pipeline_bridge import pipeline_bridge
        result = pipeline_bridge.get_imf_indicators()
        assert result["corridor_id"] == "AL_CORRIDOR_001"
        assert result["source"] == "IMF World Economic Outlook"
        assert "indicators" in result

    def test_get_imf_indicators_by_country(self):
        from src.adapters.pipeline_bridge import pipeline_bridge
        result = pipeline_bridge.get_imf_indicators(country="GHA")
        assert result["status"] in ("success", "error")

    def test_get_sovereign_risk(self):
        from src.adapters.pipeline_bridge import pipeline_bridge
        result = pipeline_bridge.get_sovereign_risk()
        assert result["corridor_id"] == "AL_CORRIDOR_001"
        assert result["status"] == "success"
        assert "cpi_scores" in result
        assert "governance" in result
        assert result["source"] == "Transparency International CPI + V-Dem"

    def test_get_sovereign_risk_by_country(self):
        from src.adapters.pipeline_bridge import pipeline_bridge
        result = pipeline_bridge.get_sovereign_risk(country="NGA")
        assert result["status"] == "success"

    def test_get_subnational_development(self):
        from src.adapters.pipeline_bridge import pipeline_bridge
        result = pipeline_bridge.get_subnational_development()
        assert result["source"] == "Global Data Lab"
        assert "regions" in result

    def test_get_development_finance(self):
        from src.adapters.pipeline_bridge import pipeline_bridge
        result = pipeline_bridge.get_development_finance()
        assert result["corridor_id"] == "AL_CORRIDOR_001"
        assert result["source"] == "AidData"
        assert result["project_count"] > 0
        assert result["total_investment_usd"] > 0

    def test_get_development_finance_by_country(self):
        from src.adapters.pipeline_bridge import pipeline_bridge
        result = pipeline_bridge.get_development_finance(country="GHA")
        assert result["status"] == "success"

    def test_get_development_finance_by_sector(self):
        from src.adapters.pipeline_bridge import pipeline_bridge
        result = pipeline_bridge.get_development_finance(sector="energy")
        assert result["status"] == "success"

    def test_get_planned_energy_projects(self):
        from src.adapters.pipeline_bridge import pipeline_bridge
        result = pipeline_bridge.get_planned_energy_projects()
        assert result["corridor_id"] == "AL_CORRIDOR_001"
        assert result["source"] == "Global Energy Monitor"
        assert result["project_count"] > 0
        assert "capacity_summary" in result

    def test_get_planned_energy_projects_by_country(self):
        from src.adapters.pipeline_bridge import pipeline_bridge
        result = pipeline_bridge.get_planned_energy_projects(country="NGA")
        assert result["status"] == "success"

    def test_get_agricultural_production(self):
        from src.adapters.pipeline_bridge import pipeline_bridge
        result = pipeline_bridge.get_agricultural_production()
        assert result["source"] == "FAO FAOSTAT"
        assert "production" in result

    def test_get_port_statistics(self):
        from src.adapters.pipeline_bridge import pipeline_bridge
        result = pipeline_bridge.get_port_statistics()
        assert result["corridor_id"] == "AL_CORRIDOR_001"
        assert result["source"] == "UNCTAD"
        assert result["port_count"] > 0
        assert "throughput_summary" in result

    def test_get_port_statistics_by_country(self):
        from src.adapters.pipeline_bridge import pipeline_bridge
        result = pipeline_bridge.get_port_statistics(country="GHA")
        assert result["status"] == "success"

    def test_get_transmission_grid(self):
        from src.adapters.pipeline_bridge import pipeline_bridge
        result = pipeline_bridge.get_transmission_grid()
        assert result["corridor_id"] == "AL_CORRIDOR_001"
        assert result["source"] == "energydata.info (World Bank ESMAP)"
        assert "grid" in result
        assert "summary" in result

    def test_get_transmission_grid_by_country(self):
        from src.adapters.pipeline_bridge import pipeline_bridge
        result = pipeline_bridge.get_transmission_grid(country="NGA")
        assert result["status"] == "success"

    def test_get_ppi_projects(self):
        from src.adapters.pipeline_bridge import pipeline_bridge
        result = pipeline_bridge.get_ppi_projects()
        assert result["corridor_id"] == "AL_CORRIDOR_001"
        assert result["source"] == "IFC PPI Database"
        assert result["project_count"] > 0
        assert "summary" in result

    def test_get_ppi_projects_by_sector(self):
        from src.adapters.pipeline_bridge import pipeline_bridge
        result = pipeline_bridge.get_ppi_projects(sector="energy")
        assert result["status"] == "success"

    def test_get_wapp_data(self):
        from src.adapters.pipeline_bridge import pipeline_bridge
        result = pipeline_bridge.get_wapp_data()
        assert result["corridor_id"] == "AL_CORRIDOR_001"
        assert result["source"] == "WAPP Master Plan"
        assert result["status"] == "success"
        assert "interconnections" in result
        assert "generation_targets" in result
        assert "trade_volumes" in result

    def test_get_wapp_data_by_country(self):
        from src.adapters.pipeline_bridge import pipeline_bridge
        result = pipeline_bridge.get_wapp_data(country="GHA")
        assert result["status"] == "success"

    def test_get_admin_boundaries(self):
        from src.adapters.pipeline_bridge import pipeline_bridge
        result = pipeline_bridge.get_admin_boundaries()
        assert result["source"] == "GADM v4.1"
        assert "regions" in result

    def test_get_flood_risk_data(self):
        from src.adapters.pipeline_bridge import pipeline_bridge
        result = pipeline_bridge.get_flood_risk_data()
        assert result["corridor_id"] == "AL_CORRIDOR_001"
        assert "source" in result

    def test_get_soil_properties(self):
        from src.adapters.pipeline_bridge import pipeline_bridge
        result = pipeline_bridge.get_soil_properties()
        assert result["corridor_id"] == "AL_CORRIDOR_001"
        assert result["source"] == "iSDAsoil Africa v1 (30m resolution)"
        assert result["status"] == "success"
        assert "clay_content" in result["available_properties"]
        assert len(result["available_properties"]) == 6
        assert len(result["depth_intervals"]) == 2
