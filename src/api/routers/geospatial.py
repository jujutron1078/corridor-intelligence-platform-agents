"""
Geospatial data endpoints for dashboard maps.

GET /api/geo/layer/{name}, /api/geo/boundaries, /api/geo/infrastructure, /api/geo/layers
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from src.api.services import geospatial_service

router = APIRouter(prefix="/api/geo", tags=["geospatial"])


@router.get("/layer/{name}")
async def get_layer(name: str):
    """Return a single GeoJSON layer by name."""
    return geospatial_service.get_layer(name)


@router.get("/boundaries")
async def boundaries():
    """Return all 5 corridor country boundaries as a single FeatureCollection."""
    return geospatial_service.get_boundaries()


@router.get("/infrastructure")
async def infrastructure():
    """Return all infrastructure GeoJSON layers for the map."""
    return geospatial_service.get_infrastructure_layers()


@router.get("/cities")
async def cities():
    """Return major corridor cities as GeoJSON."""
    return geospatial_service.get_layer("cities")


@router.get("/layers")
async def available_layers():
    """List all available geospatial layer names."""
    return {"layers": geospatial_service.get_available_layers()}
