"""Live integration tests — require API keys and external services.

Run with: pytest tests/test_live.py -m live
These are skipped by default in normal test runs.
"""

import os

import pytest

live = pytest.mark.skipif(
    not os.environ.get("RUN_LIVE_TESTS"),
    reason="Set RUN_LIVE_TESTS=1 to run live integration tests",
)


@live
class TestLiveAPI:
    @pytest.fixture(scope="class")
    def client(self):
        from src.shared.pipeline.utils import load_env
        load_env()
        from fastapi.testclient import TestClient
        from src.api.main import app
        return TestClient(app)

    def test_health_with_live_data(self, client):
        r = client.get("/api/health")
        data = r.json()
        assert data["status"] == "ok"
        assert "gee_connected" in data
        assert "datasets_loaded" in data

    def test_corridor_info_live(self, client):
        r = client.get("/api/corridor/info")
        info = r.json()
        assert len(info["nodes"]) == 13
        assert len(info["countries"]) == 5

    def test_value_chain_cocoa(self, client):
        r = client.get("/api/trade/value-chain?commodity=cocoa")
        assert r.status_code == 200
        vc = r.json()
        assert "multiplier" in vc

    def test_commodity_prices(self, client):
        for commodity in ["cocoa", "gold", "oil"]:
            r = client.get(f"/api/trade/prices?commodity={commodity}")
            assert r.status_code == 200


@live
class TestLiveGEE:
    def test_gee_sample_accra(self):
        from src.shared.pipeline.utils import load_env, get_env
        load_env()
        from src.pipelines.gee_pipeline.accessor import CorridorDataAPI
        api = CorridorDataAPI(project=get_env("GEE_PROJECT"))
        data = api.sample_at_point(lon=-0.19, lat=5.60, year=2023, month=6)
        assert "nightlights" in data
        assert "elevation" in data

    def test_gee_sample_lagos(self):
        from src.shared.pipeline.utils import load_env, get_env
        load_env()
        from src.pipelines.gee_pipeline.accessor import CorridorDataAPI
        api = CorridorDataAPI(project=get_env("GEE_PROJECT"))
        data = api.sample_at_point(lon=3.40, lat=6.45, year=2023, month=6)
        assert "nightlights" in data
        assert "population" in data
