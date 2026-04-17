"""
Infrastructure and vector data endpoints — GeoJSON.

GET /api/roads, /api/infrastructure, /api/minerals, /api/economic-anchors
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from src.api.services import osm_service, mineral_service, acled_service

router = APIRouter(prefix="/api", tags=["infrastructure"])


@router.get("/roads")
async def roads(
    tier: str = Query(None, description="Comma-separated tiers: 1,2,3,4"),
    highway: str = Query(None, description="Comma-separated OSM highway types: motorway,trunk,primary,secondary,tertiary"),
):
    """Return GeoJSON of road network filtered by tier or highway type."""
    if highway:
        types = [t.strip().lower() for t in highway.split(",") if t.strip()]
        return osm_service.get_roads_by_highway(types)
    tiers = None
    if tier:
        tiers = [int(t.strip()) for t in tier.split(",") if t.strip().isdigit()]
    return osm_service.get_roads(tiers)


@router.get("/roads/network-stats")
async def road_network_stats():
    """Return network connectivity metrics, pinch points, total km by tier."""
    return osm_service.get_network_stats()


@router.get("/infrastructure")
async def infrastructure():
    """Return GeoJSON of ports, airports, rail, border crossings, industrial zones."""
    return osm_service.get_infrastructure()


@router.get("/social")
async def social_facilities(
    type: str = Query(None, description="Filter: health, education, government, financial, religious, military, recreational"),
    source: str = Query(None, description="Filter source: osm, hdx (for health only)"),
):
    """Return GeoJSON of social infrastructure: hospitals, schools, banks, government, worship, military, recreational."""
    result = osm_service.get_social_facilities(type)

    # If requesting health with HDX source, merge or filter
    if type == "health" and source == "hdx":
        hdx = osm_service._data.get("hdx_health", {"features": []})
        return hdx
    elif type == "health" and source is None:
        # Merge OSM + HDX health data
        hdx = osm_service._data.get("hdx_health", {})
        hdx_features = hdx.get("features", [])
        for f in hdx_features:
            f_copy = dict(f)
            f_copy["properties"] = dict(f_copy.get("properties", {}))
            f_copy["properties"]["facility_type"] = "health"
            f_copy["properties"]["data_source"] = "hdx"
            result["features"].append(f_copy)

    return result


@router.get("/minerals")
async def minerals(
    commodity: str = Query(None, description="Filter by commodity: gold, bauxite, iron_ore, etc."),
    status: str = Query(None, description="Filter by status: active, developing, exploration"),
):
    """Return GeoJSON of mineral sites with commodity type, status, coordinates."""
    return mineral_service.get_minerals(commodity, status)


@router.get("/conflict")
async def conflict_events(
    country: str = Query(None, description="Filter by country name: Nigeria, Benin, Togo, Ghana, Ivory Coast"),
    year: int = Query(None, description="Filter by year"),
    event_type: str = Query(None, description="Filter: Battles, Protests, Riots, Violence against civilians, Explosions/Remote violence"),
):
    """Return GeoJSON of ACLED conflict events with summary statistics."""
    return acled_service.get_conflict_events(country, year, event_type)


@router.get("/natural-features")
async def natural_features(
    type: str = Query(None, description="Filter: rivers, lakes"),
):
    """Return GeoJSON of rivers and lakes from USGS data."""
    return mineral_service.get_natural_features(type)


@router.get("/economic-anchors")
async def economic_anchors():
    """Return unified GeoJSON combining mineral sites, ports, industrial zones, power plants, SEZs."""
    return mineral_service.get_economic_anchors()
