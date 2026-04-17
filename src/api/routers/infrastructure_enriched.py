"""
Infrastructure enriched endpoints.

GET /api/infrastructure-enriched/roads, /api/infrastructure-enriched/ports,
GET /api/infrastructure-enriched/power
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from src.api.services import infrastructure_enriched_service

router = APIRouter(prefix="/api/infrastructure-enriched", tags=["infrastructure-enriched"])


@router.get("/roads")
async def roads(
    country: str = Query(None, description="ISO3 country code: NGA, BEN, TGO, GHA, CIV"),
):
    """Return enriched road infrastructure data filtered by country."""
    return infrastructure_enriched_service.get_roads(country)


@router.get("/ports")
async def ports():
    """Return enriched port infrastructure data across all countries."""
    return infrastructure_enriched_service.get_ports()


@router.get("/power")
async def power():
    """Return enriched power infrastructure data across all countries."""
    return infrastructure_enriched_service.get_power()
