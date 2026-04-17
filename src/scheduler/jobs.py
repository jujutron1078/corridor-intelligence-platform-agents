"""Per-pipeline refresh jobs for the background data scheduler.

Each function pulls fresh data from external APIs, updates freshness.json,
and re-initialises the affected in-memory service so the API serves current
data without a restart.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from src.shared.pipeline.freshness import record_pull

logger = logging.getLogger("corridor.scheduler.jobs")


def _result(pipeline: str, success: bool, records: int = 0,
            error: str | None = None) -> dict[str, Any]:
    return {"pipeline": pipeline, "success": success,
            "records": records, "error": error}


# ── OSM ──────────────────────────────────────────────────────────────────────

def refresh_osm() -> dict[str, Any]:
    """Re-pull OSM data and reload osm_service."""
    try:
        from src.pipelines.osm_pipeline.extractor import extract_all
        from src.pipelines.osm_pipeline.config import OSM_OUTPUT_FILES, OSM_DATA_DIR
        from src.shared.pipeline.utils import save_geojson, ensure_dir

        ensure_dir(OSM_DATA_DIR)
        results = extract_all()
        total_features = 0
        for name, geojson in results.items():
            path = OSM_OUTPUT_FILES.get(name)
            if path:
                save_geojson(geojson, path)
                total_features += len(geojson["features"])
        record_pull("osm", total_features)

        from src.api.services import osm_service
        osm_service.init()

        logger.info("OSM refreshed: %d features", total_features)
        return _result("osm", True, total_features)
    except Exception as exc:
        logger.error("OSM refresh failed: %s", exc, exc_info=True)
        return _result("osm", False, error=str(exc))


# ── ACLED ────────────────────────────────────────────────────────────────────

def refresh_acled() -> dict[str, Any]:
    """Re-pull ACLED conflict events and reload acled_service."""
    try:
        from src.pipelines.acled_pipeline.fetcher import (
            fetch_all_corridor_events, save_events,
        )

        events = fetch_all_corridor_events()
        save_events(events)
        record_pull("acled", len(events))

        from src.api.services import acled_service
        acled_service.init()

        logger.info("ACLED refreshed: %d events", len(events))
        return _result("acled", True, len(events))
    except Exception as exc:
        logger.error("ACLED refresh failed: %s", exc, exc_info=True)
        return _result("acled", False, error=str(exc))


# ── Trade Prices (Pink Sheet) ────────────────────────────────────────────────

def refresh_trade_prices() -> dict[str, Any]:
    """Re-pull World Bank Pink Sheet prices and reload trade_service."""
    try:
        from src.pipelines.trade_pipeline.pinksheet import (
            download_pinksheet, parse_pinksheet, save_prices,
        )

        path = download_pinksheet()
        df = parse_pinksheet(path)
        save_prices(df)
        record_pull("trade_prices", len(df))

        from src.api.services import trade_service
        trade_service.init()

        logger.info("Trade prices refreshed: %d records", len(df))
        return _result("trade_prices", True, len(df))
    except Exception as exc:
        logger.error("Trade prices refresh failed: %s", exc, exc_info=True)
        return _result("trade_prices", False, error=str(exc))


# ── Trade Comtrade ───────────────────────────────────────────────────────────

def refresh_trade_comtrade() -> dict[str, Any]:
    """Re-pull UN Comtrade trade flows and reload trade_service."""
    try:
        comtrade_key = os.environ.get("COMTRADE_API_KEY", "")
        if not comtrade_key or comtrade_key.startswith("your-"):
            return _result("trade_comtrade", False,
                           error="COMTRADE_API_KEY not set")

        from src.pipelines.trade_pipeline.comtrade import (
            get_bilateral_flows, save_trade_data, COMMODITY_HS_CODES,
        )

        total = 0
        for commodity in COMMODITY_HS_CODES:
            df = get_bilateral_flows(commodity)
            if not df.empty:
                save_trade_data(df, f"trade_flows_{commodity}")
                total += len(df)
        record_pull("trade_comtrade", total)

        from src.api.services import trade_service
        trade_service.init()

        logger.info("Comtrade refreshed: %d records", total)
        return _result("trade_comtrade", True, total)
    except Exception as exc:
        logger.error("Comtrade refresh failed: %s", exc, exc_info=True)
        return _result("trade_comtrade", False, error=str(exc))


# ── World Bank ───────────────────────────────────────────────────────────────

def refresh_worldbank() -> dict[str, Any]:
    """Re-pull World Bank indicators and reload worldbank_service."""
    try:
        from src.pipelines.worldbank_pipeline.indicators import (
            fetch_all_indicators, save_indicators,
        )

        data = fetch_all_indicators()
        total = sum(len(v) for v in data.values())
        save_indicators(data)
        record_pull("worldbank", total)

        from src.api.services import worldbank_service
        worldbank_service.init()

        logger.info("World Bank refreshed: %d records", total)
        return _result("worldbank", True, total)
    except Exception as exc:
        logger.error("World Bank refresh failed: %s", exc, exc_info=True)
        return _result("worldbank", False, error=str(exc))


# ── Energy ───────────────────────────────────────────────────────────────────

def refresh_energy() -> dict[str, Any]:
    """Re-pull power plant database and reload energy_service."""
    try:
        from src.pipelines.energy_pipeline.downloader import download_power_plants
        from src.pipelines.energy_pipeline.processor import (
            process_power_plants, export_power_plants,
        )

        csv_path = download_power_plants()
        geojson = process_power_plants(csv_path)
        export_power_plants(geojson)
        n = len(geojson["features"])
        record_pull("energy", n)

        from src.api.services import energy_service
        energy_service.init()

        logger.info("Energy refreshed: %d plants", n)
        return _result("energy", True, n)
    except Exception as exc:
        logger.error("Energy refresh failed: %s", exc, exc_info=True)
        return _result("energy", False, error=str(exc))


# ── Minerals ─────────────────────────────────────────────────────────────────

def refresh_mineral() -> dict[str, Any]:
    """Re-pull USGS mineral geodatabase and reload mineral_service."""
    try:
        from src.pipelines.mineral_pipeline.downloader import download_geodatabase
        from src.pipelines.mineral_pipeline.processor import process_geodatabase, export_all

        result = download_geodatabase()
        if not result:
            return _result("mineral", False,
                           error="Download returned no data")

        results = process_geodatabase(result)
        export_all(results)
        total = sum(len(g.get("features", [])) for g in results.values())
        record_pull("mineral", total)

        from src.api.services import mineral_service
        mineral_service.init()

        logger.info("Minerals refreshed: %d features across %d layers", total, len(results))
        return _result("mineral", True, total)
    except Exception as exc:
        logger.error("Mineral refresh failed: %s", exc, exc_info=True)
        return _result("mineral", False, error=str(exc))


# ── Health ───────────────────────────────────────────────────────────────────

def refresh_health() -> dict[str, Any]:
    """Re-pull health facilities from healthsites.io."""
    try:
        from src.pipelines.health_pipeline.downloader import download_all_countries
        from src.pipelines.health_pipeline.processor import (
            facilities_to_geojson, save_health_facilities,
        )

        facilities = download_all_countries()
        geojson = facilities_to_geojson(facilities)
        save_health_facilities(geojson)
        n = len(geojson["features"])
        record_pull("health", n)

        logger.info("Health refreshed: %d facilities", n)
        return _result("health", True, n)
    except Exception as exc:
        logger.error("Health refresh failed: %s", exc, exc_info=True)
        return _result("health", False, error=str(exc))


# ── IMF WEO ──────────────────────────────────────────────────────────────────

def refresh_imf() -> dict[str, Any]:
    """Re-pull IMF WEO indicators."""
    try:
        from src.pipelines.imf_pipeline.fetcher import (
            fetch_all_indicators, save_indicators,
        )
        data = fetch_all_indicators()
        total = sum(len(v) for v in data.values())
        save_indicators(data)
        record_pull("imf", total)
        logger.info("IMF refreshed: %d records", total)
        return _result("imf", True, total)
    except Exception as exc:
        logger.error("IMF refresh failed: %s", exc, exc_info=True)
        return _result("imf", False, error=str(exc))


# ── CPI ──────────────────────────────────────────────────────────────────────

def refresh_cpi() -> dict[str, Any]:
    """Re-pull Transparency International CPI scores."""
    try:
        from src.pipelines.cpi_pipeline.fetcher import (
            fetch_cpi_scores, save_cpi_scores,
        )
        scores = fetch_cpi_scores()
        save_cpi_scores(scores)
        record_pull("cpi", len(scores))
        logger.info("CPI refreshed: %d country scores", len(scores))
        return _result("cpi", True, len(scores))
    except Exception as exc:
        logger.error("CPI refresh failed: %s", exc, exc_info=True)
        return _result("cpi", False, error=str(exc))


# ── V-Dem Governance ─────────────────────────────────────────────────────────

def refresh_vdem() -> dict[str, Any]:
    """Re-save V-Dem governance indicators (reference data)."""
    try:
        from src.pipelines.vdem_pipeline.fetcher import (
            get_governance_indicators, save_governance,
        )
        data = get_governance_indicators()
        save_governance(data)
        total = len(data) if isinstance(data, list) else len(data.get("countries", []))
        record_pull("vdem", total)
        logger.info("V-Dem refreshed: %d entries", total)
        return _result("vdem", True, total)
    except Exception as exc:
        logger.error("V-Dem refresh failed: %s", exc, exc_info=True)
        return _result("vdem", False, error=str(exc))


# ── Global Data Lab HDI ──────────────────────────────────────────────────────

def refresh_gdl() -> dict[str, Any]:
    """Re-pull Global Data Lab sub-national HDI."""
    try:
        from src.pipelines.gdl_pipeline.fetcher import (
            fetch_all_countries, save_subnational_hdi,
        )
        data = fetch_all_countries()
        total = sum(len(v) for v in data.values()) if isinstance(data, dict) else len(data)
        save_subnational_hdi(data)
        record_pull("gdl", total)
        logger.info("GDL refreshed: %d region records", total)
        return _result("gdl", True, total)
    except Exception as exc:
        logger.error("GDL refresh failed: %s", exc, exc_info=True)
        return _result("gdl", False, error=str(exc))


# ── AidData ──────────────────────────────────────────────────────────────────

def refresh_aiddata() -> dict[str, Any]:
    """Re-save AidData corridor projects (reference data)."""
    try:
        from src.pipelines.aiddata_pipeline.fetcher import (
            fetch_corridor_projects, save_projects,
        )
        projects = fetch_corridor_projects()
        save_projects(projects)
        record_pull("aiddata", len(projects))
        logger.info("AidData refreshed: %d projects", len(projects))
        return _result("aiddata", True, len(projects))
    except Exception as exc:
        logger.error("AidData refresh failed: %s", exc, exc_info=True)
        return _result("aiddata", False, error=str(exc))


# ── Global Energy Monitor ────────────────────────────────────────────────────

def refresh_gem() -> dict[str, Any]:
    """Re-save GEM planned energy projects (reference data)."""
    try:
        from src.pipelines.gem_pipeline.fetcher import (
            fetch_planned_projects, save_projects,
        )
        projects = fetch_planned_projects()
        save_projects(projects)
        record_pull("gem", len(projects))
        logger.info("GEM refreshed: %d projects", len(projects))
        return _result("gem", True, len(projects))
    except Exception as exc:
        logger.error("GEM refresh failed: %s", exc, exc_info=True)
        return _result("gem", False, error=str(exc))


# ── FAO FAOSTAT ──────────────────────────────────────────────────────────────

def refresh_fao() -> dict[str, Any]:
    """Re-pull FAO agricultural production data."""
    try:
        from src.pipelines.fao_pipeline.fetcher import (
            fetch_all_commodities, save_production,
        )
        data = fetch_all_commodities()
        total = sum(len(v) for v in data.values())
        save_production(data)
        record_pull("fao", total)
        logger.info("FAO refreshed: %d records", total)
        return _result("fao", True, total)
    except Exception as exc:
        logger.error("FAO refresh failed: %s", exc, exc_info=True)
        return _result("fao", False, error=str(exc))


# ── UNCTAD Port Statistics ───────────────────────────────────────────────────

def refresh_unctad() -> dict[str, Any]:
    """Re-save UNCTAD port statistics (reference data)."""
    try:
        from src.pipelines.unctad_pipeline.fetcher import (
            get_port_statistics, save_port_statistics,
        )
        ports = get_port_statistics()
        save_port_statistics(ports)
        record_pull("unctad", len(ports))
        logger.info("UNCTAD refreshed: %d ports", len(ports))
        return _result("unctad", True, len(ports))
    except Exception as exc:
        logger.error("UNCTAD refresh failed: %s", exc, exc_info=True)
        return _result("unctad", False, error=str(exc))


# ── energydata.info Grid ─────────────────────────────────────────────────────

def refresh_energydata() -> dict[str, Any]:
    """Re-pull energydata.info transmission grid data."""
    try:
        from src.pipelines.energydata_pipeline.fetcher import (
            fetch_transmission_lines, fetch_substations, save_grid_data,
        )
        lines = fetch_transmission_lines()
        subs = fetch_substations()
        data = {"transmission_lines": lines, "substations": subs}
        save_grid_data(data)
        total = len(lines) + len(subs)
        record_pull("energydata", total)
        logger.info("energydata.info refreshed: %d lines + %d substations", len(lines), len(subs))
        return _result("energydata", True, total)
    except Exception as exc:
        logger.error("energydata.info refresh failed: %s", exc, exc_info=True)
        return _result("energydata", False, error=str(exc))


# ── IFC PPI Database ─────────────────────────────────────────────────────────

def refresh_ppi() -> dict[str, Any]:
    """Re-pull IFC PPI project database."""
    try:
        from src.pipelines.ppi_pipeline.fetcher import (
            fetch_ppi_projects, save_ppi_projects,
        )
        projects = fetch_ppi_projects()
        save_ppi_projects(projects)
        record_pull("ppi", len(projects))
        logger.info("PPI refreshed: %d projects", len(projects))
        return _result("ppi", True, len(projects))
    except Exception as exc:
        logger.error("PPI refresh failed: %s", exc, exc_info=True)
        return _result("ppi", False, error=str(exc))


# ── GADM Admin Boundaries ───────────────────────────────────────────────────

def refresh_gadm() -> dict[str, Any]:
    """Re-pull GADM administrative boundaries."""
    try:
        from src.pipelines.gadm_pipeline.fetcher import (
            fetch_all_countries, save_boundaries,
        )
        data = fetch_all_countries()
        n = len(data.get("features", []))
        save_boundaries(data)
        record_pull("gadm", n)
        logger.info("GADM refreshed: %d admin regions", n)
        return _result("gadm", True, n)
    except Exception as exc:
        logger.error("GADM refresh failed: %s", exc, exc_info=True)
        return _result("gadm", False, error=str(exc))


# ── WAPP Master Plan ─────────────────────────────────────────────────────────

def refresh_wapp() -> dict[str, Any]:
    """Re-save WAPP master plan reference data."""
    try:
        from src.pipelines.wapp_pipeline.fetcher import (
            get_interconnections, get_generation_targets,
            get_trade_volumes, save_wapp_data,
        )
        data = {
            "interconnections": get_interconnections(),
            "generation_targets": get_generation_targets(),
            "trade_volumes": get_trade_volumes(),
        }
        save_wapp_data(data)
        total = len(data["interconnections"])
        record_pull("wapp", total)
        logger.info("WAPP refreshed: %d interconnections", total)
        return _result("wapp", True, total)
    except Exception as exc:
        logger.error("WAPP refresh failed: %s", exc, exc_info=True)
        return _result("wapp", False, error=str(exc))


# ── Registry ─────────────────────────────────────────────────────────────────

PIPELINE_JOBS: dict[str, callable] = {
    "osm": refresh_osm,
    "acled": refresh_acled,
    "trade_prices": refresh_trade_prices,
    "trade_comtrade": refresh_trade_comtrade,
    "worldbank": refresh_worldbank,
    "energy": refresh_energy,
    "mineral": refresh_mineral,
    "health": refresh_health,
    "imf": refresh_imf,
    "cpi": refresh_cpi,
    "vdem": refresh_vdem,
    "gdl": refresh_gdl,
    "aiddata": refresh_aiddata,
    "gem": refresh_gem,
    "fao": refresh_fao,
    "unctad": refresh_unctad,
    "energydata": refresh_energydata,
    "ppi": refresh_ppi,
    "gadm": refresh_gadm,
    "wapp": refresh_wapp,
}
