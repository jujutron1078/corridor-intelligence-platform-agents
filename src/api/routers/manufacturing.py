"""
Manufacturing companies endpoints.

GET /api/manufacturing/companies, /api/manufacturing/summary
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from src.api.services import manufacturing_service

router = APIRouter(prefix="/api/manufacturing", tags=["manufacturing"])


@router.get("/companies")
async def companies(
    country: str = Query(None, description="ISO3 country code: NGA, BEN, TGO, GHA, CIV"),
    sector: str = Query(None, description="Filter by manufacturing sector"),
):
    """Return manufacturing companies filtered by country and sector."""
    return manufacturing_service.get_companies(country, sector)


@router.get("/summary")
async def summary():
    """Return a summary of manufacturing activity across all countries."""
    return manufacturing_service.get_summary()
