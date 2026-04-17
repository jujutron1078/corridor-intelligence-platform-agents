"""
Corridor data endpoints — raster tile URLs and statistics.

GET /api/corridor/*
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query

from src.api.models.responses import TileResponse, StatsResponse, CorridorInfoResponse, LayerInfo
from src.api.services import gee_service
from src.shared.pipeline.aoi import CORRIDOR
from src.pipelines.gee_pipeline.config import DATASET_CATALOG

logger = logging.getLogger("corridor.api.corridor_router")

router = APIRouter(prefix="/api/corridor", tags=["corridor"])


@router.get("/info", response_model=CorridorInfoResponse)
async def corridor_info():
    """Return corridor metadata: AOI geometry, country list, node coordinates."""
    return CorridorInfoResponse(
        countries=CORRIDOR.countries,
        nodes=CORRIDOR.nodes,
        buffer_km=CORRIDOR.buffer_km,
        aoi_geojson=CORRIDOR.to_geojson(),
    )


@router.get("/layers", response_model=list[LayerInfo])
async def corridor_layers():
    """Return list of all available data layers with metadata."""
    layers = []
    for name, info in DATASET_CATALOG.items():
        layers.append(LayerInfo(
            name=name,
            id=name,
            type=info["type"],
            temporal_range=info["temporal"],
            resolution=info["resolution"],
            description=f"Tier {info['tier']} — {info['collection']}",
        ))
    return layers


@router.get("/nightlights", response_model=TileResponse)
async def nightlights(year: int = Query(2023), month: int = Query(6)):
    """Return GEE tile URL for nightlights + corridor-wide stats."""
    try:
        result = gee_service.get_nightlights(year, month)
        return TileResponse(
            tile_url=result["tile_url"],
            stats=result.get("stats"),
            vis_params=result.get("vis_params"),
            layer_name=result["layer_name"],
        )
    except Exception as exc:
        logger.exception("Corridor endpoint error: %s", exc)
        raise HTTPException(status_code=500, detail="Data processing error")


@router.get("/nightlights/change", response_model=TileResponse)
async def nightlights_change(year_start: int = Query(...), year_end: int = Query(...)):
    """Return tile URL for radiance change map + summary stats per country."""
    try:
        result = gee_service.get_nightlights_change(year_start, year_end)
        return TileResponse(
            tile_url=result["tile_url"],
            stats={**result.get("stats", {}), "by_country": result.get("country_stats", {})},
            vis_params=result.get("vis_params"),
            layer_name=result["layer_name"],
        )
    except Exception as exc:
        logger.exception("Corridor endpoint error: %s", exc)
        raise HTTPException(status_code=500, detail="Data processing error")


@router.get("/ndvi", response_model=TileResponse)
async def ndvi(year: int = Query(2023), month: int = Query(6)):
    """Return tile URL for NDVI layer."""
    try:
        result = gee_service.get_ndvi(year, month)
        return TileResponse(
            tile_url=result["tile_url"],
            vis_params=result.get("vis_params"),
            layer_name=result["layer_name"],
        )
    except Exception as exc:
        logger.exception("Corridor endpoint error: %s", exc)
        raise HTTPException(status_code=500, detail="Data processing error")


@router.get("/economic-index", response_model=TileResponse)
async def economic_index(year: int = Query(2023), month: int = Query(6)):
    """Return tile URL for composite economic activity index (0-1)."""
    try:
        result = gee_service.get_economic_index(year, month)
        return TileResponse(
            tile_url=result["tile_url"],
            stats=result.get("stats"),
            vis_params=result.get("vis_params"),
            layer_name=result["layer_name"],
        )
    except Exception as exc:
        logger.exception("Corridor endpoint error: %s", exc)
        raise HTTPException(status_code=500, detail="Data processing error")


@router.get("/urban-expansion", response_model=TileResponse)
async def urban_expansion(year_start: int = Query(...), year_end: int = Query(...)):
    """Return tile URL for urban expansion layer."""
    try:
        result = gee_service.get_urban_expansion(year_start, year_end)
        return TileResponse(
            tile_url=result["tile_url"],
            vis_params=result.get("vis_params"),
            layer_name=result["layer_name"],
        )
    except Exception as exc:
        logger.exception("Corridor endpoint error: %s", exc)
        raise HTTPException(status_code=500, detail="Data processing error")


@router.get("/landcover", response_model=TileResponse)
async def landcover():
    """Return tile URL for WorldCover + area stats per class."""
    try:
        result = gee_service.get_landcover()
        return TileResponse(
            tile_url=result["tile_url"],
            vis_params=result.get("vis_params"),
            layer_name=result["layer_name"],
        )
    except Exception as exc:
        logger.exception("Corridor endpoint error: %s", exc)
        raise HTTPException(status_code=500, detail="Data processing error")


@router.get("/elevation", response_model=TileResponse)
async def elevation_route():
    """Return tile URL for elevation/slope."""
    try:
        result = gee_service.get_elevation()
        return TileResponse(
            tile_url=result["tile_url"],
            vis_params=result.get("vis_params"),
            layer_name=result["layer_name"],
        )
    except Exception as exc:
        logger.exception("Corridor endpoint error: %s", exc)
        raise HTTPException(status_code=500, detail="Data processing error")


@router.get("/population", response_model=TileResponse)
async def population_route(year: int = Query(2020)):
    """Return tile URL + total population within corridor."""
    try:
        result = gee_service.get_population(year)
        return TileResponse(
            tile_url=result["tile_url"],
            stats=result.get("stats"),
            vis_params=result.get("vis_params"),
            layer_name=result["layer_name"],
        )
    except Exception as exc:
        logger.exception("Corridor endpoint error: %s", exc)
        raise HTTPException(status_code=500, detail="Data processing error")


@router.get("/forest", response_model=TileResponse)
async def forest():
    """Return tile URL for Hansen forest change + total loss area."""
    try:
        result = gee_service.get_forest()
        return TileResponse(
            tile_url=result["tile_url"],
            vis_params=result.get("vis_params"),
            layer_name=result["layer_name"],
        )
    except Exception as exc:
        logger.exception("Corridor endpoint error: %s", exc)
        raise HTTPException(status_code=500, detail="Data processing error")


@router.get("/buildings/density", response_model=TileResponse)
async def building_density():
    """Return tile URL for building density heatmap."""
    try:
        result = gee_service.get_building_density()
        return TileResponse(
            tile_url=result["tile_url"],
            vis_params=result.get("vis_params"),
            layer_name=result["layer_name"],
        )
    except Exception as exc:
        logger.exception("Corridor endpoint error: %s", exc)
        raise HTTPException(status_code=500, detail="Data processing error")


@router.get("/climate", response_model=TileResponse)
async def climate(year: int = Query(2023), month: int = Query(6)):
    """Return tile URL for temp/precip/wind."""
    try:
        result = gee_service.get_climate(year, month)
        return TileResponse(
            tile_url=result["tile_url"],
            vis_params=result.get("vis_params"),
            layer_name=result["layer_name"],
        )
    except Exception as exc:
        logger.exception("Corridor endpoint error: %s", exc)
        raise HTTPException(status_code=500, detail="Data processing error")


@router.get("/protected-areas", response_model=TileResponse)
async def protected_areas():
    """Return tile URL for WDPA protected areas overlay."""
    try:
        result = gee_service.get_protected_areas()
        return TileResponse(
            tile_url=result["tile_url"],
            vis_params=result.get("vis_params"),
            layer_name=result["layer_name"],
        )
    except Exception as exc:
        logger.exception("Corridor endpoint error: %s", exc)
        raise HTTPException(status_code=500, detail="Data processing error")


@router.get("/healthcare-access", response_model=TileResponse)
async def healthcare_access():
    """Return tile URL for healthcare accessibility (travel time in minutes)."""
    try:
        result = gee_service.get_healthcare_access()
        return TileResponse(
            tile_url=result["tile_url"],
            stats=result.get("stats"),
            vis_params=result.get("vis_params"),
            layer_name=result["layer_name"],
        )
    except Exception as exc:
        logger.exception("Corridor endpoint error: %s", exc)
        raise HTTPException(status_code=500, detail="Data processing error")


@router.get("/sample")
async def sample_point(
    lon: float = Query(...),
    lat: float = Query(...),
    year: int = Query(2023),
    month: int = Query(6),
):
    """Return all data values at a specific point including crop info if cropland."""
    try:
        result = gee_service.sample_point(lon, lat, year, month)

        # If cropland, enrich with FAO agricultural data for the country
        if result.get("landcover") == 40 or result.get("landcover_name") == "Cropland":
            country = _lon_to_country(lon)
            if country:
                result["country"] = country
                try:
                    import json
                    from src.shared.pipeline.utils import DATA_DIR
                    fao_path = DATA_DIR / "fao" / "agricultural_production.json"
                    if fao_path.exists():
                        with open(fao_path) as f:
                            fao = json.load(f)
                        crops = []
                        for crop, countries in fao.get("production", {}).items():
                            entry = countries.get(country)
                            if entry and entry.get("production_tonnes", 0) > 0:
                                crops.append({
                                    "crop": crop,
                                    "production_tonnes": entry["production_tonnes"],
                                    "area_ha": entry.get("area_harvested_ha"),
                                    "yield_kg_ha": entry.get("yield_kg_per_ha"),
                                })
                        crops.sort(key=lambda c: c["production_tonnes"], reverse=True)
                        result["agriculture"] = {
                            "country": country,
                            "note": "Specific crop at this location unknown — showing country-level production",
                            "top_crops": crops[:6],
                        }
                except Exception:
                    pass

        return result
    except Exception as exc:
        logger.exception("Corridor endpoint error: %s", exc)
        raise HTTPException(status_code=500, detail="Data processing error")


# Rough longitude-based country lookup for the corridor
def _lon_to_country(lon: float) -> str | None:
    if lon < -2.5: return "CIV"
    if lon < 0.8: return "GHA"
    if lon < 1.5: return "TGO"
    if lon < 2.6: return "BEN"
    if lon < 5.0: return "NGA"
    return None


@router.get("/transect")
async def corridor_transect(year: int = Query(2023), month: int = Query(6)):
    """Return sampled values at all 13 corridor nodes."""
    try:
        return gee_service.corridor_transect(year, month)
    except Exception as exc:
        logger.exception("Corridor endpoint error: %s", exc)
        raise HTTPException(status_code=500, detail="Data processing error")


@router.get("/stats", response_model=StatsResponse)
async def zonal_stats(
    layer: str = Query(...),
    year: int = Query(None),
    month: int = Query(None),
    group_by: str = Query("country"),
):
    """Return zonal statistics grouped by country or admin region."""
    try:
        stats = gee_service.zone_stats(layer, year, month, group_by)
        return StatsResponse(layer=layer, stats=stats, group_by=group_by)
    except Exception as exc:
        logger.exception("Corridor endpoint error: %s", exc)
        raise HTTPException(status_code=500, detail="Data processing error")
