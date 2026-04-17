"""
Tourism endpoints.

GET /api/tourism/indicators, /api/tourism/comparison
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from src.api.services import tourism_service

router = APIRouter(prefix="/api/tourism", tags=["tourism"])


@router.get("/indicators")
async def indicators(
    country: str = Query(None, description="ISO3 country code: NGA, BEN, TGO, GHA, CIV"),
):
    """Return tourism indicators filtered by country."""
    return tourism_service.get_indicators(country)


@router.get("/comparison")
async def comparison():
    """Return a cross-country tourism comparison."""
    return tourism_service.get_comparison()
