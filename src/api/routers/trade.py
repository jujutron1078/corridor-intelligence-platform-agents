"""
Trade & commodity data endpoints.

GET /api/trade/*
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from src.api.services import trade_service

router = APIRouter(prefix="/api/trade", tags=["trade"])


@router.get("/flows")
async def trade_flows(
    country: str = Query(..., description="ISO3 code: NGA, BEN, TGO, GHA, CIV"),
    commodity: str = Query(..., description="Commodity: cocoa, gold, oil, etc."),
):
    """Return trade flow data: export volumes, destinations, raw vs. processed split."""
    return trade_service.get_trade_flows(country, commodity)


@router.get("/arcs")
async def trade_arcs(
    country: str = Query(..., description="ISO3 code: NGA, BEN, TGO, GHA, CIV"),
    commodity: str = Query(..., description="Commodity: cocoa, gold, oil, etc."),
    top_n: int = Query(8, description="Top N partners per flow direction"),
):
    """Return trade flow arcs with source/target coordinates for map visualization."""
    return trade_service.get_trade_arcs(country, commodity, top_n)


@router.get("/partners")
async def top_partners(
    country: str = Query(..., description="ISO3 code: NGA, BEN, TGO, GHA, CIV"),
    commodity: str = Query(..., description="Commodity: cocoa, gold, oil, etc."),
    flow: str = Query("export", description="export or import"),
    top_n: int = Query(10, description="Number of top partners"),
):
    """Return top trade partners by value for a country/commodity."""
    return trade_service.get_top_partners(country, commodity, flow, top_n)


@router.get("/value-chain")
async def value_chain(
    commodity: str = Query(..., description="Commodity: cocoa, gold, bauxite, rubber, timber, oil"),
):
    """Return value-chain analysis: raw price, processed price, multiplier, gap per country."""
    return trade_service.get_value_chain(commodity)


@router.get("/prices")
async def commodity_prices(
    commodity: str = Query(...),
    start: int = Query(2015),
    end: int = Query(2024),
):
    """Return monthly price time-series (for charts)."""
    return trade_service.get_commodity_prices(commodity, start, end)
