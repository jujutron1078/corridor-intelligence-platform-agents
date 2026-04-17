"""
Agriculture enriched endpoints.

GET /api/agriculture-enriched/crops, /api/agriculture-enriched/summary
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from src.api.services import agriculture_enriched_service

router = APIRouter(prefix="/api/agriculture-enriched", tags=["agriculture-enriched"])


@router.get("/crops")
async def crops(
    country: str = Query(None, description="ISO3 country code: NGA, BEN, TGO, GHA, CIV"),
    crop: str = Query(None, description="Filter by crop type"),
):
    """Return enriched crop data filtered by country and crop type."""
    return agriculture_enriched_service.get_crops(country, crop)


@router.get("/summary")
async def summary():
    """Return an enriched agriculture summary across all countries."""
    return agriculture_enriched_service.get_summary()
