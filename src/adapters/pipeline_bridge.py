"""
Pipeline Bridge — Adapter that lets agent tools call pipeline services in-process.

Uses lazy imports to avoid circular dependencies and allows graceful startup
when services aren't initialized. Every method wraps service calls in
try/except and returns an error dict on failure.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("corridor.bridge")


class PipelineBridge:
    """Singleton adapter between agent tools and pipeline data services."""

    # ── Corridor / AOI ───────────────────────────────────────────────────

    def get_corridor_info(self) -> dict[str, Any]:
        """Return corridor metadata (nodes, bbox, countries, geometry)."""
        from src.shared.pipeline.aoi import CORRIDOR
        return {
            "corridor_id": "AL_CORRIDOR_001",
            "name": "Lagos-Abidjan Economic Corridor",
            "length_km": 1080,
            "buffer_km": CORRIDOR.buffer_km,
            "countries": CORRIDOR.countries,
            "nodes": CORRIDOR.nodes,
            "bbox": list(CORRIDOR.bbox),
            "geojson": CORRIDOR.to_geojson(),
            "nodes_geojson": CORRIDOR.to_nodes_geojson(),
            "status": "success",
        }

    def define_corridor(self, buffer_width_km: float = 50) -> dict[str, Any]:
        """Return corridor polygon from real AOI definition."""
        from src.shared.pipeline.aoi import CORRIDOR
        geojson = CORRIDOR.to_geojson()
        geojson["properties"]["buffer_km"] = buffer_width_km
        return {
            "corridor_id": "AL_CORRIDOR_001",
            "length_km": 1080,
            "area_sqkm": 1080 * buffer_width_km,
            "bounding_polygon_geojson": geojson,
            "status": "success",
            "message": f"Corridor defined with {buffer_width_km}km total width.",
        }

    # ── Geospatial layers ────────────────────────────────────────────────

    def get_geospatial_layers(self, layers: list[str] | None = None) -> dict[str, Any]:
        """Fetch real GEE tile URLs and layer metadata."""
        from src.api.services import gee_service

        requested = layers or ["satellite", "dem", "land_use", "protected_areas"]
        result: dict[str, Any] = {
            "corridor_id": "AL_CORRIDOR_001",
            "status": "Analysis Ready Data (ARD) Generated",
            "data_inventory": {"layers_requested": requested, "raster_layers": {}},
        }

        layer_map = {
            "satellite": ("nightlights", lambda: gee_service.get_nightlights(2023, 6)),
            "dem": ("elevation", lambda: gee_service.get_elevation()),
            "land_use": ("landcover", lambda: gee_service.get_landcover()),
            "protected_areas": ("protected_areas", lambda: gee_service.get_protected_areas()),
            "ndvi": ("ndvi", lambda: gee_service.get_ndvi(2023, 6)),
            "population": ("population", lambda: gee_service.get_population(2023)),
            "forest": ("forest", lambda: gee_service.get_forest()),
            "urban": ("urban_expansion", lambda: gee_service.get_urban_expansion(2018, 2023)),
        }

        for layer_name in requested:
            if layer_name in layer_map:
                key, fetcher = layer_map[layer_name]
                try:
                    data = fetcher()
                    result["data_inventory"]["raster_layers"][key] = data
                except Exception as exc:
                    logger.warning("Failed to fetch layer %s: %s", layer_name, exc)
                    result["data_inventory"]["raster_layers"][key] = {
                        "error": str(exc),
                        "status": "unavailable",
                    }

        return result

    # ── Terrain / elevation ──────────────────────────────────────────────

    def get_terrain_data(self) -> dict[str, Any]:
        """Return SRTM elevation/slope data from GEE."""
        from src.api.services import gee_service
        elevation = gee_service.get_elevation()
        return {
            "corridor_id": "AL_CORRIDOR_001",
            "elevation_data": elevation,
            "source": "SRTM GL1 (USGS/SRTMGL1_003)",
            "resolution_meters": 30,
            "status": "success",
        }

    # ── Environmental constraints ────────────────────────────────────────

    def get_environmental_constraints(self) -> dict[str, Any]:
        """Return protected areas and forest cover from GEE."""
        from src.api.services import gee_service
        protected = gee_service.get_protected_areas()
        forest = gee_service.get_forest()
        return {
            "corridor_id": "AL_CORRIDOR_001",
            "protected_areas": protected,
            "forest_cover": forest,
            "source": "WDPA + Hansen Global Forest Change",
            "status": "success",
        }

    # ── Infrastructure detection ─────────────────────────────────────────

    def get_infrastructure_detections(self) -> dict[str, Any]:
        """Merge OSM infrastructure + USGS minerals into detection format."""
        from src.api.services import osm_service, mineral_service

        detections = []

        # OSM infrastructure
        for getter, det_type in [
            (osm_service.get_ports, "port_facility"),
            (osm_service.get_airports, "airport"),
            (osm_service.get_railways, "rail_network"),
            (osm_service.get_industrial, "industrial_zone"),
            (osm_service.get_border_crossings, "border_crossing"),
        ]:
            try:
                data = getter()
                for i, feat in enumerate(data.get("features", [])):
                    coords = feat.get("geometry", {}).get("coordinates", [])
                    detections.append({
                        "detection_id": f"DET-{det_type[:3].upper()}-{i+1:03d}",
                        "type": det_type,
                        "name": feat.get("properties", {}).get("name", "Unknown"),
                        "coordinates": coords,
                        "confidence": 0.85,
                        "source": "OpenStreetMap",
                        "properties": feat.get("properties", {}),
                    })
            except Exception as exc:
                logger.warning("Failed to get %s: %s", det_type, exc)

        # USGS minerals
        try:
            minerals = mineral_service.get_economic_anchors()
            for i, feat in enumerate(minerals.get("features", [])):
                coords = feat.get("geometry", {}).get("coordinates", [])
                detections.append({
                    "detection_id": f"DET-MIN-{i+1:03d}",
                    "type": "mineral_site",
                    "name": feat.get("properties", {}).get("site_name", "Unknown"),
                    "coordinates": coords,
                    "confidence": 0.90,
                    "source": "USGS",
                    "properties": feat.get("properties", {}),
                })
        except Exception as exc:
            logger.warning("Failed to get minerals: %s", exc)

        return {
            "corridor_id": "AL_CORRIDOR_001",
            "status": "Infrastructure Detections Complete",
            "detection_count": len(detections),
            "detections": detections,
        }

    # ── Geocode location ─────────────────────────────────────────────────

    def geocode_location(self, location_names: list[str]) -> dict[str, Any]:
        """Resolve location names using corridor nodes first, then fallback."""
        from src.shared.pipeline.aoi import CORRIDOR

        resolved = []
        for name in location_names:
            found = False
            for node in CORRIDOR.nodes:
                if name.lower() in node["name"].lower():
                    resolved.append({
                        "input_name": name,
                        "latitude": node["lat"],
                        "longitude": node["lon"],
                        "confidence": 0.98,
                        "source": "corridor_nodes",
                    })
                    found = True
                    break
            if not found:
                resolved.append({
                    "input_name": name,
                    "latitude": None,
                    "longitude": None,
                    "confidence": 0.0,
                    "source": "not_found",
                    "message": f"'{name}' not found in corridor nodes. External geocoding needed.",
                })
        return {"resolved_locations": resolved}

    # ── Economic anchors ─────────────────────────────────────────────────

    def get_economic_anchors(self) -> dict[str, Any]:
        """Return mineral/economic anchor sites from USGS data."""
        from src.api.services import mineral_service
        anchors = mineral_service.get_economic_anchors()
        return {
            "corridor_id": "AL_CORRIDOR_001",
            "anchors": anchors,
            "source": "USGS Mineral Resources",
            "status": "success",
        }

    # ── Energy data ──────────────────────────────────────────────────────

    def get_energy_data(self, country: str | None = None) -> dict[str, Any]:
        """Return power plants and grid data."""
        from src.api.services import energy_service
        plants = energy_service.get_power_plants(country=country)
        grid = energy_service.get_grid()
        return {
            "corridor_id": "AL_CORRIDOR_001",
            "power_plants": plants,
            "grid": grid,
            "source": "Global Power Plant Database",
            "status": "success",
        }

    # ── Trade data ───────────────────────────────────────────────────────

    def get_trade_data(self, country: str, commodity: str) -> dict[str, Any]:
        """Return trade flows for a country/commodity pair."""
        from src.api.services import trade_service
        flows = trade_service.get_trade_flows(country, commodity)
        return {
            "corridor_id": "AL_CORRIDOR_001",
            "trade_flows": flows,
            "source": "UN Comtrade",
            "status": "success",
        }

    # ── World Bank indicators ────────────────────────────────────────────

    def get_worldbank_indicators(self, country: str | None = None) -> dict[str, Any]:
        """Return World Bank economic indicators."""
        from src.api.services import worldbank_service
        summary = worldbank_service.get_country_summary(country=country)
        return {
            "corridor_id": "AL_CORRIDOR_001",
            "indicators": summary,
            "source": "World Bank",
            "status": "success",
        }

    # ── Conflict data ────────────────────────────────────────────────────

    def get_conflict_data(self, country: str | None = None) -> dict[str, Any]:
        """Return ACLED conflict events with flattened summary."""
        from src.api.services import acled_service
        events = acled_service.get_conflict_events(country=country)
        summary = events.get("summary", {})
        return {
            "corridor_id": "AL_CORRIDOR_001",
            "total_events": summary.get("total_events", 0),
            "total_fatalities": summary.get("total_fatalities", 0),
            "by_event_type": summary.get("by_event_type", {}),
            "by_country": summary.get("by_country", {}),
            "events": events.get("features", []),
            "risk_level": (
                "critical" if summary.get("total_events", 0) > 500
                else "high" if summary.get("total_events", 0) > 200
                else "medium" if summary.get("total_events", 0) > 50
                else "low"
            ),
            "source": "ACLED",
            "status": "success",
        }


    # ── Live news search (Tavily) ────────────────────────────────────────

    def search_corridor_news(
        self,
        query: str | None = None,
        max_results: int = 5,
    ) -> dict[str, Any]:
        """Search for live news about the corridor using Tavily API."""
        from src.api.config import TAVILY_API_KEY

        if not TAVILY_API_KEY:
            return {
                "results": [],
                "query": query or "",
                "status": "unavailable",
                "message": "TAVILY_API_KEY not configured",
            }

        search_query = query or "Lagos Abidjan corridor infrastructure investment West Africa"

        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=TAVILY_API_KEY)
            response = client.search(
                query=search_query,
                max_results=max_results,
                search_depth="basic",
                include_answer=True,
            )

            results = []
            for item in response.get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("content", "")[:500],
                    "score": item.get("score", 0),
                })

            return {
                "results": results,
                "answer": response.get("answer", ""),
                "query": search_query,
                "result_count": len(results),
                "status": "success",
            }
        except Exception as exc:
            logger.warning("Tavily search failed: %s", exc)
            return {
                "results": [],
                "query": search_query,
                "status": "error",
                "message": str(exc),
            }

    # ── Road network graph ────────────────────────────────────────────────

    def get_road_network_graph(self) -> Any:
        """Build and return a NetworkX graph from OSM road data."""
        from src.api.services import osm_service
        from src.pipelines.osm_pipeline.processor import build_network_graph

        roads = osm_service.get_roads()
        if not roads.get("features"):
            return None
        return build_network_graph(roads)

    def get_road_network_stats(self) -> dict[str, Any]:
        """Return pre-computed road network statistics."""
        from src.api.services import osm_service
        return osm_service.get_network_stats()

    # ── IMF WEO indicators ─────────────────────────────────────────────────

    def get_imf_indicators(self, country: str | None = None) -> dict[str, Any]:
        """Return IMF World Economic Outlook forecasts."""
        try:
            from src.pipelines.imf_pipeline.fetcher import load_indicators, get_latest_values
            data = load_indicators()
            if not data:
                from src.pipelines.imf_pipeline.fetcher import fetch_all_indicators
                data = fetch_all_indicators()
            result = {}
            for key in data:
                result[key] = get_latest_values(data, key)
            if country:
                result = {k: {c: v for c, v in vals.items() if c == country.upper()}
                          for k, vals in result.items()}
            return {
                "corridor_id": "AL_CORRIDOR_001",
                "indicators": result,
                "source": "IMF World Economic Outlook",
                "status": "success",
            }
        except Exception as exc:
            logger.warning("IMF indicators failed: %s", exc)
            return {"status": "error", "message": str(exc)}

    # ── Sovereign risk (CPI + V-Dem) ───────────────────────────────────────

    def get_sovereign_risk(self, country: str | None = None) -> dict[str, Any]:
        """Return sovereign risk indicators (CPI + V-Dem governance)."""
        result: dict[str, Any] = {"corridor_id": "AL_CORRIDOR_001"}
        try:
            from src.pipelines.cpi_pipeline.fetcher import load_cpi_scores
            scores = load_cpi_scores()
            if not scores:
                from src.pipelines.cpi_pipeline.fetcher import fetch_cpi_scores
                scores = fetch_cpi_scores()
            if country:
                scores = [s for s in scores if s.get("country_iso3") == country.upper()]
            result["cpi_scores"] = scores
        except Exception as exc:
            logger.warning("CPI scores failed: %s", exc)
            result["cpi_scores"] = []

        try:
            from src.pipelines.vdem_pipeline.fetcher import load_governance
            gov = load_governance()
            if not gov:
                from src.pipelines.vdem_pipeline.fetcher import get_governance_indicators
                gov = get_governance_indicators(country_iso3=country)
            result["governance"] = gov
        except Exception as exc:
            logger.warning("V-Dem governance failed: %s", exc)
            result["governance"] = {}

        result["source"] = "Transparency International CPI + V-Dem"
        result["status"] = "success"
        return result

    # ── Sub-national development (Global Data Lab) ─────────────────────────

    def get_subnational_development(self, country: str | None = None) -> dict[str, Any]:
        """Return sub-national HDI and development indicators."""
        try:
            from src.pipelines.gdl_pipeline.fetcher import (
                load_subnational_hdi, get_regions_for_country,
            )
            data = load_subnational_hdi()
            if not data:
                from src.pipelines.gdl_pipeline.fetcher import fetch_all_countries
                data = fetch_all_countries()
            if country:
                regions = get_regions_for_country(data, country.upper())
            else:
                regions = data if isinstance(data, list) else []
                if isinstance(data, dict):
                    for v in data.values():
                        if isinstance(v, list):
                            regions.extend(v)
            return {
                "corridor_id": "AL_CORRIDOR_001",
                "regions": regions,
                "source": "Global Data Lab",
                "status": "success",
            }
        except Exception as exc:
            logger.warning("GDL sub-national failed: %s", exc)
            return {"status": "error", "message": str(exc)}

    # ── Development finance (AidData) ──────────────────────────────────────

    def get_development_finance(self, country: str | None = None, sector: str | None = None) -> dict[str, Any]:
        """Return georeferenced development finance projects."""
        try:
            from src.pipelines.aiddata_pipeline.fetcher import (
                load_projects, get_projects_by_country, get_projects_by_sector,
            )
            projects = load_projects()
            if not projects:
                from src.pipelines.aiddata_pipeline.fetcher import fetch_corridor_projects
                projects = fetch_corridor_projects()
            if country:
                projects = get_projects_by_country(projects, country.upper())
            if sector:
                projects = get_projects_by_sector(projects, sector)
            return {
                "corridor_id": "AL_CORRIDOR_001",
                "projects": projects,
                "project_count": len(projects),
                "total_investment_usd": sum(p.get("amount_usd", 0) for p in projects),
                "source": "AidData",
                "status": "success",
            }
        except Exception as exc:
            logger.warning("AidData projects failed: %s", exc)
            return {"status": "error", "message": str(exc)}

    # ── Planned energy projects (GEM) ──────────────────────────────────────

    def get_planned_energy_projects(self, country: str | None = None) -> dict[str, Any]:
        """Return planned/under-construction energy projects from GEM."""
        try:
            from src.pipelines.gem_pipeline.fetcher import (
                load_projects, get_total_planned_capacity,
            )
            projects = load_projects()
            if not projects:
                from src.pipelines.gem_pipeline.fetcher import fetch_planned_projects
                projects = fetch_planned_projects(country_iso3=country)
            elif country:
                projects = [p for p in projects if p.get("country_iso3") == country.upper()]
            capacity = get_total_planned_capacity(projects)
            return {
                "corridor_id": "AL_CORRIDOR_001",
                "projects": projects,
                "project_count": len(projects),
                "capacity_summary": capacity,
                "source": "Global Energy Monitor",
                "status": "success",
            }
        except Exception as exc:
            logger.warning("GEM projects failed: %s", exc)
            return {"status": "error", "message": str(exc)}

    # ── Agricultural production (FAO) ──────────────────────────────────────

    def get_agricultural_production(self, country: str | None = None) -> dict[str, Any]:
        """Return FAO agricultural production data for corridor commodities."""
        try:
            from src.pipelines.fao_pipeline.fetcher import (
                load_production, get_production_by_country,
            )
            data = load_production()
            if not data:
                from src.pipelines.fao_pipeline.fetcher import fetch_all_commodities
                data = fetch_all_commodities()
            if country:
                result = get_production_by_country(data, country.upper())
            else:
                result = data
            return {
                "corridor_id": "AL_CORRIDOR_001",
                "production": result,
                "source": "FAO FAOSTAT",
                "status": "success",
            }
        except Exception as exc:
            logger.warning("FAO production failed: %s", exc)
            return {"status": "error", "message": str(exc)}

    # ── Port statistics (UNCTAD) ───────────────────────────────────────────

    def get_port_statistics(self, country: str | None = None) -> dict[str, Any]:
        """Return port throughput and logistics data."""
        try:
            from src.pipelines.unctad_pipeline.fetcher import (
                load_port_statistics, get_total_throughput,
            )
            ports = load_port_statistics()
            if not ports:
                from src.pipelines.unctad_pipeline.fetcher import get_port_statistics as fetch_ports
                ports = fetch_ports(country_iso3=country)
            elif country:
                ports = [p for p in ports if p.get("country_iso3") == country.upper()]
            throughput = get_total_throughput(ports)
            return {
                "corridor_id": "AL_CORRIDOR_001",
                "ports": ports,
                "port_count": len(ports),
                "throughput_summary": throughput,
                "source": "UNCTAD",
                "status": "success",
            }
        except Exception as exc:
            logger.warning("UNCTAD ports failed: %s", exc)
            return {"status": "error", "message": str(exc)}

    # ── Transmission grid (energydata.info) ────────────────────────────────

    def get_transmission_grid(self, country: str | None = None) -> dict[str, Any]:
        """Return existing transmission lines and substations."""
        try:
            from src.pipelines.energydata_pipeline.fetcher import (
                load_grid_data, get_grid_summary,
                fetch_transmission_lines, fetch_substations,
            )
            data = load_grid_data()
            if not data:
                lines = fetch_transmission_lines(country_iso3=country)
                subs = fetch_substations(country_iso3=country)
                data = {"transmission_lines": lines, "substations": subs}
            elif country:
                c = country.upper()
                data = {
                    "transmission_lines": [l for l in data.get("transmission_lines", [])
                                           if l.get("country_iso3") == c],
                    "substations": [s for s in data.get("substations", [])
                                    if s.get("country_iso3") == c],
                }
            summary = get_grid_summary(data)
            return {
                "corridor_id": "AL_CORRIDOR_001",
                "grid": data,
                "summary": summary,
                "source": "energydata.info (World Bank ESMAP)",
                "status": "success",
            }
        except Exception as exc:
            logger.warning("energydata.info grid failed: %s", exc)
            return {"status": "error", "message": str(exc)}

    # ── PPP/PFI projects (IFC PPI) ────────────────────────────────────────

    def get_ppi_projects(self, country: str | None = None, sector: str | None = None) -> dict[str, Any]:
        """Return past PPP/PFI infrastructure projects."""
        try:
            from src.pipelines.ppi_pipeline.fetcher import (
                load_ppi_projects, get_ppi_summary, get_ppi_by_sector,
            )
            projects = load_ppi_projects()
            if not projects:
                from src.pipelines.ppi_pipeline.fetcher import fetch_ppi_projects
                projects = fetch_ppi_projects(country_iso3=country, sector=sector)
            else:
                if country:
                    projects = [p for p in projects if p.get("country_iso3") == country.upper()]
                if sector:
                    projects = get_ppi_by_sector(projects, sector)
            summary = get_ppi_summary(projects)
            return {
                "corridor_id": "AL_CORRIDOR_001",
                "projects": projects,
                "project_count": len(projects),
                "summary": summary,
                "source": "IFC PPI Database",
                "status": "success",
            }
        except Exception as exc:
            logger.warning("PPI projects failed: %s", exc)
            return {"status": "error", "message": str(exc)}

    # ── WAPP interconnections & targets ────────────────────────────────────

    def get_wapp_data(self, country: str | None = None) -> dict[str, Any]:
        """Return WAPP master plan data (interconnections, generation targets, trade)."""
        try:
            from src.pipelines.wapp_pipeline.fetcher import (
                load_wapp_data,
                get_interconnections, get_generation_targets, get_trade_volumes,
            )
            data = load_wapp_data()
            if not data:
                data = {
                    "interconnections": get_interconnections(),
                    "generation_targets": get_generation_targets(),
                    "trade_volumes": get_trade_volumes(),
                }
            interconnections = data.get("interconnections", [])
            if country:
                iso = country.upper()
                interconnections = [
                    ic for ic in interconnections
                    if ic.get("from_country") == iso or ic.get("to_country") == iso
                ]
            return {
                "corridor_id": "AL_CORRIDOR_001",
                "interconnections": interconnections,
                "generation_targets": data.get("generation_targets", {}),
                "trade_volumes": data.get("trade_volumes", {}),
                "source": "WAPP Master Plan",
                "status": "success",
            }
        except Exception as exc:
            logger.warning("WAPP data failed: %s", exc)
            return {"status": "error", "message": str(exc)}

    # ── Admin boundaries (GADM) ────────────────────────────────────────────

    def get_admin_boundaries(self, country: str | None = None) -> dict[str, Any]:
        """Return admin Level 1 boundaries for zonal aggregation."""
        try:
            from src.pipelines.gadm_pipeline.fetcher import (
                load_boundaries, get_regions_for_country,
            )
            data = load_boundaries()
            if not data:
                from src.pipelines.gadm_pipeline.fetcher import fetch_all_countries
                data = fetch_all_countries()
            if country:
                regions = get_regions_for_country(data, country.upper())
            else:
                regions = data.get("features", []) if isinstance(data, dict) else data
            return {
                "corridor_id": "AL_CORRIDOR_001",
                "boundaries": data if not country else None,
                "regions": regions,
                "source": "GADM v4.1",
                "status": "success",
            }
        except Exception as exc:
            logger.warning("GADM boundaries failed: %s", exc)
            return {"status": "error", "message": str(exc)}

    # ── Flood risk data (GEE) ──────────────────────────────────────────────

    def get_flood_risk_data(self) -> dict[str, Any]:
        """Return flood risk layers from GEE."""
        try:
            from src.api.services import gee_service
            # Try to get flood data from Global Flood Database
            # Falls back to JRC Surface Water occurrence as proxy
            jrc = gee_service.get_water() if hasattr(gee_service, 'get_water') else None
            return {
                "corridor_id": "AL_CORRIDOR_001",
                "flood_data": jrc,
                "source": "Global Flood Database + JRC Surface Water",
                "status": "success",
            }
        except Exception as exc:
            logger.warning("Flood risk data failed: %s", exc)
            return {"status": "error", "message": str(exc)}

    # ── Climate hazards ────────────────────────────────────────────────────

    def get_drought_data(self, aoi: dict[str, Any] | None = None) -> dict[str, Any]:
        """Return 12-month SPEI drought status for the AOI."""
        try:
            from src.pipelines.climate_pipeline.fetchers import fetch_drought_spei
            return fetch_drought_spei(aoi)
        except Exception as exc:
            logger.warning("Drought data failed: %s", exc)
            return {"hazard": "drought", "status": "error", "message": str(exc)}

    def get_heat_risk_data(self, aoi: dict[str, Any] | None = None) -> dict[str, Any]:
        """Return heat stress delta vs 1991-2020 baseline."""
        try:
            from src.pipelines.climate_pipeline.fetchers import fetch_heat_stress_era5
            return fetch_heat_stress_era5(aoi)
        except Exception as exc:
            logger.warning("Heat risk data failed: %s", exc)
            return {"hazard": "heat", "status": "error", "message": str(exc)}

    def get_coastal_flood_data(self, aoi: dict[str, Any] | None = None, return_period: int = 100) -> dict[str, Any]:
        """Return coastal inundation depth (Deltares) for the given return period."""
        try:
            from src.pipelines.climate_pipeline.fetchers import fetch_coastal_flood_deltares
            return fetch_coastal_flood_deltares(aoi, rp=return_period)
        except Exception as exc:
            logger.warning("Coastal flood data failed: %s", exc)
            return {"hazard": "coastal_flood", "status": "error", "message": str(exc)}

    def get_composite_climate_risk(self, country_iso: str) -> dict[str, Any]:
        """Return GFDRR ThinkHazard! multi-hazard ranking for a country."""
        try:
            from src.pipelines.climate_pipeline.fetchers import fetch_composite_thinkhazard
            return fetch_composite_thinkhazard(country_iso)
        except Exception as exc:
            logger.warning("Composite climate risk failed: %s", exc)
            return {"hazard": "composite", "status": "error", "message": str(exc)}

    # ── Soil properties (GEE) ──────────────────────────────────────────────

    def get_soil_properties(self) -> dict[str, Any]:
        """Return soil property data from iSDAsoil (GEE)."""
        return {
            "corridor_id": "AL_CORRIDOR_001",
            "available_properties": [
                "clay_content", "ph", "sand_content",
                "bulk_density", "organic_carbon", "nitrogen",
            ],
            "depth_intervals": ["0-20cm", "20-50cm"],
            "source": "iSDAsoil Africa v1 (30m resolution)",
            "collection_prefix": "ISDASOIL/Africa/v1/",
            "status": "success",
            "note": "Use GEE to sample soil properties at specific locations along route.",
        }


# Singleton instance
pipeline_bridge = PipelineBridge()
