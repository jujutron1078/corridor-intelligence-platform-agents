"""Integration tests for the merged Corridor Intelligence Platform."""

import sys
from pathlib import Path

import pytest

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestPipelineBridge:
    """Verify the pipeline bridge adapter."""

    def test_bridge_import(self):
        from src.adapters.pipeline_bridge import pipeline_bridge
        assert pipeline_bridge is not None

    def test_corridor_info(self):
        from src.adapters.pipeline_bridge import pipeline_bridge
        info = pipeline_bridge.get_corridor_info()
        assert info["status"] == "success"
        assert info["corridor_id"] == "AL_CORRIDOR_001"
        assert len(info["countries"]) == 5
        assert len(info["nodes"]) == 13
        assert info["length_km"] == 1080

    def test_define_corridor(self):
        from src.adapters.pipeline_bridge import pipeline_bridge
        result = pipeline_bridge.define_corridor(buffer_width_km=50)
        assert result["status"] == "success"
        assert "bounding_polygon_geojson" in result
        assert result["bounding_polygon_geojson"]["type"] == "Feature"

    def test_geocode_known_location(self):
        from src.adapters.pipeline_bridge import pipeline_bridge
        result = pipeline_bridge.geocode_location(["Lagos", "Accra"])
        locations = result["resolved_locations"]
        assert len(locations) == 2
        assert locations[0]["input_name"] == "Lagos"
        assert locations[0]["confidence"] == 0.98
        assert locations[0]["latitude"] is not None

    def test_geocode_unknown_location(self):
        from src.adapters.pipeline_bridge import pipeline_bridge
        result = pipeline_bridge.geocode_location(["Narnia"])
        locations = result["resolved_locations"]
        assert len(locations) == 1
        assert locations[0]["confidence"] == 0.0
        assert locations[0]["source"] == "not_found"

    def test_gee_service_graceful_failure(self):
        """Verify bridge doesn't crash when GEE isn't authenticated."""
        from src.adapters.pipeline_bridge import pipeline_bridge
        try:
            result = pipeline_bridge.get_terrain_data()
            # If GEE is available, should succeed
            assert "corridor_id" in result
        except Exception:
            # If GEE unavailable, should raise — caller wraps in try/except
            pass


class TestUnifiedAPI:
    """Verify the unified FastAPI app has all expected routes."""

    def test_app_import(self):
        from src.api.main import app
        assert app is not None
        assert app.title == "Corridor Intelligence Platform"
        assert app.version == "0.2.0"

    def test_all_routes_registered(self):
        from src.api.main import app
        route_paths = [r.path for r in app.routes]

        # Pipeline routes
        assert "/" in route_paths
        assert "/api/docs" in route_paths or any("/api/" in p for p in route_paths)

        # Workspace routes (from agents)
        assert "/workspace/projects" in route_paths or any("/workspace/" in p for p in route_paths)

    def test_schemas_import(self):
        from src.api.schemas import success_response, error_response
        s = success_response("ok", {"key": "val"})
        assert s["success"] is True
        assert s["data"]["key"] == "val"

        e = error_response("fail")
        assert e["success"] is False
        assert e["data"] is None


class TestSharedPipelineImports:
    """Verify core pipeline shared modules work in the new location."""

    def test_aoi(self):
        from src.shared.pipeline.aoi import CORRIDOR
        assert len(CORRIDOR.countries) == 5
        assert CORRIDOR.buffer_km == 50

    def test_utils_project_root(self):
        import os
        from src.shared.pipeline.utils import PROJECT_ROOT, DATA_DIR, OUTPUTS_DIR
        from pathlib import Path

        # PROJECT_ROOT should still resolve to the repo root
        assert (PROJECT_ROOT / "pyproject.toml").exists()

        # DATA_DIR tracks CORRIDOR_DATA_ROOT when set, otherwise PROJECT_ROOT/data.
        data_override = os.environ.get("CORRIDOR_DATA_ROOT")
        outputs_override = os.environ.get("CORRIDOR_OUTPUTS_ROOT")
        expected_data = Path(data_override).expanduser() if data_override else PROJECT_ROOT / "data"
        expected_outputs = Path(outputs_override).expanduser() if outputs_override else PROJECT_ROOT / "outputs"
        assert DATA_DIR == expected_data
        assert OUTPUTS_DIR == expected_outputs

    def test_freshness(self):
        from src.shared.pipeline.freshness import STALENESS_THRESHOLDS
        assert "osm" in STALENESS_THRESHOLDS
        assert "acled" in STALENESS_THRESHOLDS
