"""
Macro enriched endpoints.

GET /api/macro-enriched/indicators, /api/macro-enriched/trade-composition
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from src.api.services import macro_enriched_service

router = APIRouter(prefix="/api/macro-enriched", tags=["macro-enriched"])


@router.get("/indicators")
async def indicators(
    country: str = Query(None, description="ISO3 country code: NGA, BEN, TGO, GHA, CIV"),
):
    """Return enriched macroeconomic indicators filtered by country."""
    return macro_enriched_service.get_indicators(country)


@router.get("/trade-composition")
async def trade_composition():
    """Return enriched trade composition data across all countries."""
    return macro_enriched_service.get_trade_composition()
