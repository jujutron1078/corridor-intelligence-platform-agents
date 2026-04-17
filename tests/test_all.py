"""Comprehensive test suite for the Corridor Intelligence Platform."""

import sys
import time
from pathlib import Path

import pytest

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ── Module Imports: Core ────────────────────────────────────────────────────

class TestCoreImports:
    def test_shared_aoi(self):
        __import__("src.shared.pipeline.aoi")

    def test_shared_utils(self):
        __import__("src.shared.pipeline.utils")

    def test_gee_config(self):
        __import__("src.pipelines.gee_pipeline.config")

    def test_gee_processors(self):
        __import__("src.pipelines.gee_pipeline.processors")

    def test_gee_accessor(self):
        __import__("src.pipelines.gee_pipeline.accessor")

    def test_osm_config(self):
        __import__("src.pipelines.osm_pipeline.config")

    def test_osm_extractor(self):
        __import__("src.pipelines.osm_pipeline.extractor")

    def test_osm_processor(self):
        __import__("src.pipelines.osm_pipeline.processor")

    def test_mineral_downloader(self):
        __import__("src.pipelines.mineral_pipeline.downloader")

    def test_mineral_processor(self):
        __import__("src.pipelines.mineral_pipeline.processor")

    def test_trade_comtrade(self):
        __import__("src.pipelines.trade_pipeline.comtrade")

    def test_trade_pinksheet(self):
        __import__("src.pipelines.trade_pipeline.pinksheet")

    def test_trade_value_chain(self):
        __import__("src.pipelines.trade_pipeline.value_chain")

    def test_catalog_catalog(self):
        __import__("src.catalog.catalog")

    def test_catalog_validator(self):
        __import__("src.catalog.validator")

    def test_catalog_report(self):
        __import__("src.catalog.report")


# ── Module Imports: New Pipelines ───────────────────────────────────────────

class TestNewPipelineImports:
    def test_worldbank_pipeline(self):
        __import__("src.pipelines.worldbank_pipeline")

    def test_worldbank_indicators(self):
        __import__("src.pipelines.worldbank_pipeline.indicators")

    def test_worldbank_pipeline_cli(self):
        __import__("src.pipelines.worldbank_pipeline.pipeline")

    def test_acled_pipeline(self):
        __import__("src.pipelines.acled_pipeline")

    def test_acled_fetcher(self):
        __import__("src.pipelines.acled_pipeline.fetcher")

    def test_acled_pipeline_cli(self):
        __import__("src.pipelines.acled_pipeline.pipeline")

    def test_energy_pipeline(self):
        __import__("src.pipelines.energy_pipeline")

    def test_energy_downloader(self):
        __import__("src.pipelines.energy_pipeline.downloader")

    def test_energy_processor(self):
        __import__("src.pipelines.energy_pipeline.processor")

    def test_energy_pipeline_cli(self):
        __import__("src.pipelines.energy_pipeline.pipeline")

    def test_livestock_pipeline(self):
        __import__("src.pipelines.livestock_pipeline")

    def test_livestock_downloader(self):
        __import__("src.pipelines.livestock_pipeline.downloader")

    def test_livestock_processor(self):
        __import__("src.pipelines.livestock_pipeline.processor")

    def test_livestock_pipeline_cli(self):
        __import__("src.pipelines.livestock_pipeline.pipeline")

    def test_connectivity_pipeline(self):
        __import__("src.pipelines.connectivity_pipeline")

    def test_connectivity_downloader(self):
        __import__("src.pipelines.connectivity_pipeline.downloader")

    def test_connectivity_processor(self):
        __import__("src.pipelines.connectivity_pipeline.processor")

    def test_connectivity_pipeline_cli(self):
        __import__("src.pipelines.connectivity_pipeline.pipeline")

    def test_health_pipeline(self):
        __import__("src.pipelines.health_pipeline")

    def test_health_downloader(self):
        __import__("src.pipelines.health_pipeline.downloader")

    def test_health_processor(self):
        __import__("src.pipelines.health_pipeline.processor")

    def test_health_pipeline_cli(self):
        __import__("src.pipelines.health_pipeline.pipeline")


# ── Module Imports: Enriched Pipelines ────────────────────────────────────

class TestEnrichedPipelineImports:
    def test_imf_pipeline(self):
        __import__("src.pipelines.imf_pipeline.fetcher")

    def test_cpi_pipeline(self):
        __import__("src.pipelines.cpi_pipeline.fetcher")

    def test_vdem_pipeline(self):
        __import__("src.pipelines.vdem_pipeline.fetcher")

    def test_gdl_pipeline(self):
        __import__("src.pipelines.gdl_pipeline.fetcher")

    def test_aiddata_pipeline(self):
        __import__("src.pipelines.aiddata_pipeline.fetcher")

    def test_gem_pipeline(self):
        __import__("src.pipelines.gem_pipeline.fetcher")

    def test_fao_pipeline(self):
        __import__("src.pipelines.fao_pipeline.fetcher")

    def test_unctad_pipeline(self):
        __import__("src.pipelines.unctad_pipeline.fetcher")

    def test_energydata_pipeline(self):
        __import__("src.pipelines.energydata_pipeline.fetcher")

    def test_ppi_pipeline(self):
        __import__("src.pipelines.ppi_pipeline.fetcher")

    def test_gadm_pipeline(self):
        __import__("src.pipelines.gadm_pipeline.fetcher")

    def test_wapp_pipeline(self):
        __import__("src.pipelines.wapp_pipeline.fetcher")


# ── Module Imports: API ─────────────────────────────────────────────────────

class TestAPIImports:
    def test_api_config(self):
        __import__("src.api.config")

    def test_api_cache(self):
        __import__("src.api.cache")

    def test_api_models_requests(self):
        __import__("src.api.models.requests")

    def test_api_models_responses(self):
        __import__("src.api.models.responses")

    def test_api_services_llm(self):
        __import__("src.api.services.llm_service")

    def test_api_services_chat(self):
        __import__("src.api.services.chat_service")

    def test_api_services_worldbank(self):
        __import__("src.api.services.worldbank_service")

    def test_api_services_acled(self):
        __import__("src.api.services.acled_service")

    def test_api_services_energy(self):
        __import__("src.api.services.energy_service")

    def test_api_services_livestock(self):
        __import__("src.api.services.livestock_service")

    def test_api_services_connectivity(self):
        __import__("src.api.services.connectivity_service")

    def test_api_routers_indicators(self):
        __import__("src.api.routers.indicators")

    def test_api_routers_energy(self):
        __import__("src.api.routers.energy")

    def test_api_main(self):
        __import__("src.api.main")


# ── Corridor AOI ────────────────────────────────────────────────────────────

class TestCorridorAOI:
    def test_13_nodes(self):
        from src.shared.pipeline.aoi import CORRIDOR
        assert len(CORRIDOR.nodes) == 13

    def test_5_countries(self):
        from src.shared.pipeline.aoi import CORRIDOR
        assert len(CORRIDOR.countries) == 5

    def test_centerline_is_linestring(self):
        from src.shared.pipeline.aoi import CORRIDOR
        assert CORRIDOR.centerline.geom_type == "LineString"

    def test_buffered_polygon(self):
        from src.shared.pipeline.aoi import CORRIDOR
        assert CORRIDOR.buffered_polygon.geom_type == "Polygon"

    def test_geojson_export(self):
        from src.shared.pipeline.aoi import CORRIDOR
        assert CORRIDOR.to_geojson()["type"] == "Feature"

    def test_nodes_geojson_13_features(self):
        from src.shared.pipeline.aoi import CORRIDOR
        assert len(CORRIDOR.to_nodes_geojson()["features"]) == 13


# ── GEE Config ──────────────────────────────────────────────────────────────

class TestGEEConfig:
    def test_17_datasets(self):
        from src.pipelines.gee_pipeline.config import DATASET_CATALOG
        assert len(DATASET_CATALOG) == 17

    def test_8_tier1(self):
        from src.pipelines.gee_pipeline.config import DATASET_CATALOG
        assert sum(1 for v in DATASET_CATALOG.values() if v["tier"] == 1) == 8

    def test_9_tier2(self):
        from src.pipelines.gee_pipeline.config import DATASET_CATALOG
        assert sum(1 for v in DATASET_CATALOG.values() if v["tier"] == 2) == 9

    def test_24_vis_palettes(self):
        from src.pipelines.gee_pipeline.config import VIS_PARAMS
        assert len(VIS_PARAMS) == 24

    def test_6_test_points(self):
        from src.pipelines.gee_pipeline.config import TEST_POINTS
        assert len(TEST_POINTS) == 6

    def test_wdpa_collection(self):
        from src.pipelines.gee_pipeline.config import WDPA_COLLECTION
        assert WDPA_COLLECTION == "WCMC/WDPA/current/polygons"

    def test_healthcare_access_image(self):
        from src.pipelines.gee_pipeline.config import HEALTHCARE_ACCESS_IMAGE
        assert "malariaatlasproject" in HEALTHCARE_ACCESS_IMAGE or "Oxford/MAP" in HEALTHCARE_ACCESS_IMAGE


# ── OSM Pipeline ────────────────────────────────────────────────────────────

class TestOSMPipeline:
    def test_15_queries(self):
        from src.pipelines.osm_pipeline.config import QUERIES
        assert len(QUERIES) == 15

    def test_4_road_tiers(self):
        from src.pipelines.osm_pipeline.config import ROAD_TIERS
        assert len(ROAD_TIERS) == 4

    def test_13_highway_mappings(self):
        from src.pipelines.osm_pipeline.config import HIGHWAY_TO_TIER
        assert len(HIGHWAY_TO_TIER) == 13

    def test_haversine_lagos_abidjan(self):
        from src.pipelines.osm_pipeline.processor import _haversine
        dist = _haversine(3.40, 6.45, -3.97, 5.36)
        assert 800 < dist < 850

    def test_military_query(self):
        from src.pipelines.osm_pipeline.config import QUERIES
        assert "military" in QUERIES

    def test_recreational_query(self):
        from src.pipelines.osm_pipeline.config import QUERIES
        assert "recreational" in QUERIES

    def test_military_output_path(self):
        from src.pipelines.osm_pipeline.config import OSM_OUTPUT_FILES
        assert "military" in OSM_OUTPUT_FILES

    def test_recreational_output_path(self):
        from src.pipelines.osm_pipeline.config import OSM_OUTPUT_FILES
        assert "recreational" in OSM_OUTPUT_FILES


class TestRoadClassification:
    @pytest.fixture()
    def classified_roads(self):
        from src.pipelines.osm_pipeline.processor import classify_roads
        test_roads = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"highway": "motorway", "surface": "asphalt"},
                    "geometry": {"type": "LineString", "coordinates": [[3.40, 6.45], [2.63, 6.46]]},
                },
                {
                    "type": "Feature",
                    "properties": {"highway": "tertiary"},
                    "geometry": {"type": "LineString", "coordinates": [[1.23, 6.17], [1.10, 6.13]]},
                },
                {
                    "type": "Feature",
                    "properties": {"highway": "residential"},
                    "geometry": {"type": "LineString", "coordinates": [[-0.19, 5.60], [-1.02, 5.10]]},
                },
            ],
        }
        return classify_roads(test_roads)

    def test_motorway_tier1(self, classified_roads):
        assert classified_roads["features"][0]["properties"]["tier"] == 1

    def test_tertiary_tier3(self, classified_roads):
        assert classified_roads["features"][1]["properties"]["tier"] == 3

    def test_residential_tier4(self, classified_roads):
        assert classified_roads["features"][2]["properties"]["tier"] == 4

    def test_road_length_computed(self, classified_roads):
        assert classified_roads["features"][0]["properties"]["length_km"] > 0

    def test_surface_preserved(self, classified_roads):
        assert classified_roads["features"][0]["properties"]["surface"] == "asphalt"

    def test_network_graph(self, classified_roads):
        from src.pipelines.osm_pipeline.processor import build_network_graph, compute_network_stats
        G = build_network_graph(classified_roads)
        stats = compute_network_stats(G)
        assert stats["total_nodes"] > 0
        assert stats["total_km"] > 0


# ── Mineral Pipeline ────────────────────────────────────────────────────────

class TestMineralPipeline:
    def test_classify_gold(self):
        from src.pipelines.mineral_pipeline.processor import classify_commodity
        assert classify_commodity("Gold mine") == "gold"

    def test_classify_bauxite(self):
        from src.pipelines.mineral_pipeline.processor import classify_commodity
        assert classify_commodity("Bauxite deposit") == "bauxite"

    def test_classify_iron_ore(self):
        from src.pipelines.mineral_pipeline.processor import classify_commodity
        assert classify_commodity("Iron ore") == "iron_ore"

    def test_classify_crude_oil(self):
        from src.pipelines.mineral_pipeline.processor import classify_commodity
        assert classify_commodity("Crude oil") == "oil_gas"

    def test_classify_unknown(self):
        from src.pipelines.mineral_pipeline.processor import classify_commodity
        assert classify_commodity("Unknown stuff") == "other"

    def test_status_active(self):
        from src.pipelines.mineral_pipeline.processor import classify_status
        assert classify_status("Active mine") == "active"

    def test_status_construction(self):
        from src.pipelines.mineral_pipeline.processor import classify_status
        assert classify_status("Under construction") == "developing"

    def test_economic_anchors(self):
        from src.pipelines.mineral_pipeline.processor import create_economic_anchors
        anchors = create_economic_anchors(
            mineral_geojson={"type": "FeatureCollection", "features": [
                {"type": "Feature", "properties": {"name": "Mine A"}, "geometry": {"type": "Point", "coordinates": [0, 0]}}
            ]},
            ports_geojson={"type": "FeatureCollection", "features": [
                {"type": "Feature", "properties": {"name": "Port B"}, "geometry": {"type": "Point", "coordinates": [1, 1]}}
            ]},
        )
        assert len(anchors["features"]) == 2
        assert anchors["features"][0]["properties"]["anchor_type"] == "mineral"


# ── Trade Pipeline ──────────────────────────────────────────────────────────

class TestTradePipeline:
    def test_6_commodity_families(self):
        from src.pipelines.trade_pipeline.comtrade import COMMODITY_HS_CODES
        assert len(COMMODITY_HS_CODES) == 6

    def test_5_m49_countries(self):
        from src.pipelines.trade_pipeline.comtrade import COUNTRY_M49
        assert len(COUNTRY_M49) == 5

    def test_6_processing_multipliers(self):
        from src.pipelines.trade_pipeline.value_chain import PROCESSING_MULTIPLIERS
        assert len(PROCESSING_MULTIPLIERS) == 6

    def test_cocoa_value_chain(self):
        from src.pipelines.trade_pipeline.value_chain import compute_value_chain_gap
        cocoa = compute_value_chain_gap("cocoa")
        assert cocoa["multiplier"] == 3.2
        assert len(cocoa["gaps_by_country"]) == 5
        assert cocoa["gaps_by_country"]["CIV"]["processing_pct"] == 35

    def test_oil_value_chain(self):
        from src.pipelines.trade_pipeline.value_chain import compute_value_chain_gap
        oil = compute_value_chain_gap("oil")
        assert oil["multiplier"] == 1.8

    def test_bauxite_value_chain(self):
        from src.pipelines.trade_pipeline.value_chain import compute_value_chain_gap
        bauxite = compute_value_chain_gap("bauxite")
        assert bauxite["multiplier"] == 8.5


# ── World Bank Pipeline ────────────────────────────────────────────────────

class TestWorldBankPipeline:
    def test_13_indicators(self):
        from src.pipelines.worldbank_pipeline.indicators import INDICATORS
        assert len(INDICATORS) == 13

    def test_gdp_indicator(self):
        from src.pipelines.worldbank_pipeline.indicators import INDICATORS
        assert "GDP" in INDICATORS

    def test_fdi_indicator(self):
        from src.pipelines.worldbank_pipeline.indicators import INDICATORS
        assert "FDI" in INDICATORS

    def test_trade_pct_gdp(self):
        from src.pipelines.worldbank_pipeline.indicators import INDICATORS
        assert "TRADE_PCT_GDP" in INDICATORS

    def test_electricity_access(self):
        from src.pipelines.worldbank_pipeline.indicators import INDICATORS
        assert "ELECTRICITY_ACCESS" in INDICATORS

    def test_internet_users(self):
        from src.pipelines.worldbank_pipeline.indicators import INDICATORS
        assert "INTERNET_USERS" in INDICATORS

    def test_5_countries(self):
        from src.pipelines.worldbank_pipeline.indicators import COUNTRY_NAMES
        assert len(COUNTRY_NAMES) == 5

    def test_nga_is_nigeria(self):
        from src.pipelines.worldbank_pipeline.indicators import COUNTRY_NAMES
        assert COUNTRY_NAMES["NGA"] == "Nigeria"


# ── ACLED Pipeline ──────────────────────────────────────────────────────────

class TestACLEDPipeline:
    def test_5_countries(self):
        from src.pipelines.acled_pipeline.fetcher import CORRIDOR_COUNTRIES
        assert len(CORRIDOR_COUNTRIES) == 5

    def test_6_event_types(self):
        from src.pipelines.acled_pipeline.fetcher import EVENT_TYPES
        assert len(EVENT_TYPES) == 6

    def test_battles_in_types(self):
        from src.pipelines.acled_pipeline.fetcher import EVENT_TYPES
        assert "Battles" in EVENT_TYPES

    def test_events_to_geojson(self):
        from src.pipelines.acled_pipeline.fetcher import events_to_geojson
        mock_events = [
            {"longitude": "3.40", "latitude": "6.45", "event_id_cnty": "1", "event_date": "2024-01-15",
             "year": "2024", "event_type": "Battles", "sub_event_type": "Armed clash",
             "actor1": "A", "actor2": "B", "country": "Nigeria", "admin1": "Lagos",
             "admin2": "", "location": "Lagos", "fatalities": "5", "notes": "test"},
        ]
        gj = events_to_geojson(mock_events)
        assert gj["type"] == "FeatureCollection"
        assert len(gj["features"]) == 1
        assert gj["features"][0]["properties"]["fatalities"] == 5


# ── Energy Pipeline ─────────────────────────────────────────────────────────

class TestEnergyPipeline:
    def test_14_fuel_categories(self):
        from src.pipelines.energy_pipeline.processor import FUEL_CATEGORIES
        assert len(FUEL_CATEGORIES) >= 14

    def test_5_countries(self):
        from src.pipelines.energy_pipeline.processor import CORRIDOR_COUNTRIES
        assert len(CORRIDOR_COUNTRIES) == 5

    def test_energy_summary(self):
        from src.pipelines.energy_pipeline.processor import get_energy_summary
        mock_energy = {"type": "FeatureCollection", "features": [
            {"type": "Feature", "geometry": {"type": "Point", "coordinates": [0, 0]},
             "properties": {"capacity_mw": 100, "fuel_category": "solar", "country": "NGA"}},
            {"type": "Feature", "geometry": {"type": "Point", "coordinates": [1, 1]},
             "properties": {"capacity_mw": 50, "fuel_category": "gas", "country": "GHA"}},
        ]}
        summary = get_energy_summary(mock_energy)
        assert summary["total_plants"] == 2
        assert summary["total_capacity_mw"] == 150
        assert len(summary["by_fuel"]) == 2


# ── Livestock Pipeline ──────────────────────────────────────────────────────

class TestLivestockPipeline:
    def test_5_species(self):
        from src.pipelines.livestock_pipeline.downloader import SPECIES_URLS
        assert len(SPECIES_URLS) == 5

    def test_cattle_in_species(self):
        from src.pipelines.livestock_pipeline.downloader import SPECIES_URLS
        assert "cattle" in SPECIES_URLS

    def test_goats_in_species(self):
        from src.pipelines.livestock_pipeline.downloader import SPECIES_URLS
        assert "goats" in SPECIES_URLS


# ── Connectivity Pipeline ───────────────────────────────────────────────────

class TestConnectivityPipeline:
    def test_connectivity_summary(self):
        from src.pipelines.connectivity_pipeline.processor import get_connectivity_summary
        mock = {"type": "FeatureCollection", "features": [
            {"type": "Feature", "geometry": {"type": "Point", "coordinates": [0, 0]},
             "properties": {"avg_download_mbps": 25.5, "avg_upload_mbps": 5.0, "avg_latency_ms": 30, "tests": 100, "devices": 50}},
        ]}
        summary = get_connectivity_summary(mock)
        assert summary["total_tiles"] == 1
        assert summary["avg_download_mbps"] == 25.5


# ── Health Pipeline ─────────────────────────────────────────────────────────

class TestHealthPipeline:
    def test_facilities_to_geojson(self):
        from src.pipelines.health_pipeline.processor import facilities_to_geojson
        mock = {"NGA": [
            {"geometry": {"type": "Point", "coordinates": [3.40, 6.45]},
             "properties": {"name": "Hospital A", "amenity": "hospital", "uuid": "123"}},
        ]}
        gj = facilities_to_geojson(mock)
        assert gj["type"] == "FeatureCollection"
        assert len(gj["features"]) == 1


# ── Data Freshness ─────────────────────────────────────────────────────────

class TestFreshness:
    def test_import(self):
        __import__("src.shared.pipeline.freshness")

    def test_staleness_thresholds(self):
        from src.shared.pipeline.freshness import STALENESS_THRESHOLDS
        assert len(STALENESS_THRESHOLDS) >= 20

    def test_record_and_read(self, tmp_path, monkeypatch):
        import src.shared.pipeline.freshness as fm
        monkeypatch.setattr(fm, "FRESHNESS_PATH", tmp_path / "freshness.json")
        fm.record_pull("test_pipeline", 42)
        data = fm.load_freshness()
        assert data["test_pipeline"]["records"] == 42
        assert data["test_pipeline"]["pulled_at"] is not None

    def test_age_days_none_when_missing(self, tmp_path, monkeypatch):
        import src.shared.pipeline.freshness as fm
        monkeypatch.setattr(fm, "FRESHNESS_PATH", tmp_path / "freshness.json")
        assert fm.age_days("nonexistent") is None

    def test_is_stale_when_never_pulled(self, tmp_path, monkeypatch):
        import src.shared.pipeline.freshness as fm
        monkeypatch.setattr(fm, "FRESHNESS_PATH", tmp_path / "freshness.json")
        assert fm.is_stale("osm") is True

    def test_not_stale_after_fresh_pull(self, tmp_path, monkeypatch):
        import src.shared.pipeline.freshness as fm
        monkeypatch.setattr(fm, "FRESHNESS_PATH", tmp_path / "freshness.json")
        fm.record_pull("osm", 100)
        assert fm.is_stale("osm") is False

    def test_freshness_report_keys(self, tmp_path, monkeypatch):
        import src.shared.pipeline.freshness as fm
        monkeypatch.setattr(fm, "FRESHNESS_PATH", tmp_path / "freshness.json")
        report = fm.get_freshness_report()
        assert "osm" in report
        assert "acled" in report
        for entry in report.values():
            assert "stale" in entry
            assert "max_age_days" in entry


# ── Data Catalog ────────────────────────────────────────────────────────────

class TestDataCatalog:
    def test_42_plus_sources(self):
        from src.catalog.catalog import get_catalog
        assert len(get_catalog()) >= 42

    def test_17_gee_sources(self):
        from src.catalog.catalog import get_catalog_by_type, SourceType
        assert len(get_catalog_by_type(SourceType.GEE)) == 17

    def test_2_osm_sources(self):
        from src.catalog.catalog import get_catalog_by_type, SourceType
        assert len(get_catalog_by_type(SourceType.OSM)) == 2

    def test_1_usgs_source(self):
        from src.catalog.catalog import get_catalog_by_type, SourceType
        assert len(get_catalog_by_type(SourceType.USGS)) == 1

    def test_18_plus_api_sources(self):
        from src.catalog.catalog import get_catalog_by_type, SourceType
        assert len(get_catalog_by_type(SourceType.API)) >= 18

    def test_3_manual_sources(self):
        from src.catalog.catalog import get_catalog_by_type, SourceType
        assert len(get_catalog_by_type(SourceType.MANUAL)) == 3

    def test_report_generated(self):
        from src.catalog.report import generate_report
        report = generate_report()
        assert len(report) > 100

    def test_report_has_known_gaps(self):
        from src.catalog.report import generate_report
        assert "Known Data Gaps" in generate_report()

    def test_report_mentions_worldpop(self):
        from src.catalog.report import generate_report
        assert "WorldPop" in generate_report()


# ── API Cache ───────────────────────────────────────────────────────────────

class TestAPICache:
    def test_set_get(self):
        from src.api.cache import TTLCache
        cache = TTLCache(default_ttl=10, max_size=100)
        cache.set("k1", "v1")
        assert cache.get("k1") == "v1"

    def test_miss_returns_none(self):
        from src.api.cache import TTLCache
        cache = TTLCache(default_ttl=10, max_size=100)
        assert cache.get("missing") is None

    def test_stats_size(self):
        from src.api.cache import TTLCache
        cache = TTLCache(default_ttl=10, max_size=100)
        cache.set("k1", "v1")
        assert cache.stats["size"] == 1

    def test_ttl_expiry(self):
        from src.api.cache import TTLCache
        cache = TTLCache(default_ttl=1, max_size=3)
        cache.set("expire", "val", ttl=1)
        assert cache.get("expire") == "val"
        time.sleep(1.1)
        assert cache.get("expire") is None

    def test_make_cache_key(self):
        from src.api.cache import make_cache_key
        assert make_cache_key("nl", 2023, 6) == "nl:2023:6"


# ── Pydantic Models ────────────────────────────────────────────────────────

class TestPydanticModels:
    def test_chat_request(self):
        from src.api.models.requests import ChatRequest
        req = ChatRequest(message="test query")
        assert req.message == "test query"

    def test_chat_response(self):
        from src.api.models.responses import ChatResponse
        resp = ChatResponse(response="hello", model_used="test-model")
        assert resp.response == "hello"

    def test_map_layer(self):
        from src.api.models.responses import MapLayer
        layer = MapLayer(id="nl", type="raster", tile_url="http://x", name="Test")
        assert layer.id == "nl" and layer.type == "raster"

    def test_health_response(self):
        from src.api.models.responses import HealthResponse
        health = HealthResponse(gee_connected=True, datasets_loaded=13)
        assert health.gee_connected and health.datasets_loaded == 13

    def test_chat_request_rejects_empty(self):
        from src.api.models.requests import ChatRequest
        with pytest.raises(Exception):
            ChatRequest(message="")

    def test_chat_response_chart_data_defaults_to_list(self):
        from src.api.models.responses import ChatResponse
        resp = ChatResponse(response="hello", model_used="test")
        assert resp.chart_data == []
        assert isinstance(resp.chart_data, list)

    def test_chat_response_chart_data_accepts_list(self):
        from src.api.models.responses import ChatResponse, ChartData
        chart = ChartData(type="bar", title="Test", data=[{"x": 1}], x_key="x", y_key="y")
        resp = ChatResponse(response="hi", model_used="m", chart_data=[chart])
        assert len(resp.chart_data) == 1
        assert resp.chart_data[0].title == "Test"

    def test_tool_result_dataclass(self):
        from src.api.services.chat_service import ToolResult
        tr = ToolResult(text="hello")
        assert tr.text == "hello"
        assert tr.map_layer is None
        assert tr.chart is None
        assert tr.points == []

    def test_geojson_to_datapoints(self):
        from src.api.services.chat_service import _geojson_to_datapoints
        geojson = {"type": "FeatureCollection", "features": [
            {"type": "Feature", "geometry": {"type": "Point", "coordinates": [3.4, 6.5]},
             "properties": {"name": "Test Point", "value": 42}},
            {"type": "Feature", "geometry": {"type": "LineString", "coordinates": [[0, 0], [1, 1]]},
             "properties": {"name": "Not a point"}},
        ]}
        points = _geojson_to_datapoints(geojson)
        assert len(points) == 1
        assert points[0].lon == 3.4
        assert points[0].lat == 6.5
        assert points[0].name == "Test Point"

    def test_geojson_to_datapoints_limit(self):
        from src.api.services.chat_service import _geojson_to_datapoints
        geojson = {"type": "FeatureCollection", "features": [
            {"type": "Feature", "geometry": {"type": "Point", "coordinates": [i, i]},
             "properties": {"name": f"P{i}"}}
            for i in range(10)
        ]}
        points = _geojson_to_datapoints(geojson, limit=3)
        assert len(points) == 3

    @pytest.mark.parametrize("msg", [
        "Show me a chart of cocoa prices",
        "Graph GDP over time",
        "Compare nightlights 2015 vs 2022",
        "What is the trend in FDI?",
        "Plot power plant distribution",
        "Visualize trade breakdown",
        "cocoa price time-series",
    ])
    def test_wants_chart_true(self, msg):
        from src.api.services.chat_service import _wants_chart
        assert _wants_chart(msg) is True

    @pytest.mark.parametrize("msg", [
        "Show power plants in Nigeria",
        "What are cocoa prices?",
        "Show mineral sites in Ghana",
        "Hello",
        "What is the GDP of Nigeria?",
    ])
    def test_wants_chart_false(self, msg):
        from src.api.services.chat_service import _wants_chart
        assert _wants_chart(msg) is False


# ── Model Routing ───────────────────────────────────────────────────────────

class TestModelRouting:
    def test_6_routes(self):
        from src.api.config import MODEL_ROUTES
        assert len(MODEL_ROUTES) == 6

    def test_chat_agent_route(self):
        from src.api.config import MODEL_ROUTES
        assert "chat_agent" in MODEL_ROUTES

    def test_synthesis_route(self):
        from src.api.config import MODEL_ROUTES
        assert "synthesis" in MODEL_ROUTES

    def test_simple_route(self):
        from src.api.config import MODEL_ROUTES
        assert "simple" in MODEL_ROUTES

    def test_report_route(self):
        from src.api.config import MODEL_ROUTES
        assert "report" in MODEL_ROUTES

    def test_all_have_fallback(self):
        from src.api.config import MODEL_ROUTES
        assert all("fallback" in v for v in MODEL_ROUTES.values())

    def test_all_have_temperature(self):
        from src.api.config import MODEL_ROUTES
        assert all("temperature" in v for v in MODEL_ROUTES.values())


# ── Chat Service ────────────────────────────────────────────────────────────

class TestChatService:
    def test_25_plus_tools(self):
        from src.api.services.chat_service import DATA_TOOLS
        assert len(DATA_TOOLS) >= 25

    def test_system_prompt_length(self):
        from src.api.services.chat_service import CORRIDOR_SYSTEM_PROMPT
        assert len(CORRIDOR_SYSTEM_PROMPT) > 2000

    @pytest.mark.parametrize("tool_name", [
        "get_nightlights", "get_value_chain", "sample_point",
        "get_corridor_transect", "get_protected_areas", "get_healthcare_access",
        "get_country_indicators", "get_country_summary", "get_conflict_events",
        "get_power_plants", "get_livestock", "get_connectivity",
        "get_social_facilities",
    ])
    def test_tool_present(self, tool_name):
        from src.api.services.chat_service import DATA_TOOLS
        tool_names = [t["function"]["name"] for t in DATA_TOOLS]
        assert tool_name in tool_names


# ── FastAPI HTTP Endpoints ──────────────────────────────────────────────────

class TestHTTPEndpoints:
    @pytest.fixture(scope="class")
    def client(self):
        from fastapi.testclient import TestClient
        from src.api.main import app
        return TestClient(app)

    @pytest.mark.parametrize("path", [
        "/",
        "/api/health",
        "/api/usage",
        "/api/corridor/info",
        "/api/corridor/layers",
        "/api/roads",
        "/api/roads?tier=1,2",
        "/api/roads/network-stats",
        "/api/infrastructure",
        "/api/minerals",
        "/api/minerals?commodity=gold",
        "/api/economic-anchors",
        "/api/trade/value-chain?commodity=cocoa",
        "/api/trade/prices?commodity=cocoa",
        "/api/social",
        "/api/social?type=military",
        "/api/conflict",
        "/api/indicators/available",
        "/api/indicators?indicator=GDP",
        "/api/indicators/summary?country=NGA",
        "/api/indicators/livestock",
        "/api/indicators/connectivity",
        "/api/energy/plants",
        "/api/energy/grid",
    ])
    def test_endpoint_200(self, client, path):
        assert client.get(path).status_code == 200


class TestHTTPContent:
    @pytest.fixture(scope="class")
    def client(self):
        from fastapi.testclient import TestClient
        from src.api.main import app
        return TestClient(app)

    def test_info_13_nodes(self, client):
        info = client.get("/api/corridor/info").json()
        assert len(info["nodes"]) == 13

    def test_info_5_countries(self, client):
        info = client.get("/api/corridor/info").json()
        assert len(info["countries"]) == 5

    def test_info_has_aoi_geojson(self, client):
        info = client.get("/api/corridor/info").json()
        assert "aoi_geojson" in info

    def test_info_buffer_50km(self, client):
        info = client.get("/api/corridor/info").json()
        assert info["buffer_km"] == 50.0

    def test_17_layers(self, client):
        layers = client.get("/api/corridor/layers").json()
        assert len(layers) == 17

    def test_health_status_ok(self, client):
        data = client.get("/api/health").json()
        assert data["status"] == "ok"

    def test_health_6_model_routes(self, client):
        data = client.get("/api/health").json()
        assert len(data["model_routes"]) == 6

    def test_cocoa_value_chain(self, client):
        vc = client.get("/api/trade/value-chain?commodity=cocoa").json()
        assert vc["multiplier"] == 3.2
        assert "gaps_by_country" in vc

    def test_13_indicators_available(self, client):
        available = client.get("/api/indicators/available").json()
        assert len(available) == 13
