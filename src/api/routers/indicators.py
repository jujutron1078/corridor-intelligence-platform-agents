"""
Economic and social indicators endpoints.

GET /api/indicators, /api/indicators/summary, /api/indicators/available
GET /api/livestock, /api/connectivity
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from src.api.services import worldbank_service, livestock_service, connectivity_service

router = APIRouter(prefix="/api/indicators", tags=["indicators"])


@router.get("/available")
async def available_indicators():
    """Return list of all available World Bank indicators."""
    return worldbank_service.get_available_indicators()


@router.get("")
async def indicators(
    indicator: str = Query(..., description="Indicator key: GDP, FDI, TRADE_PCT_GDP, REMITTANCES, etc."),
    country: str = Query(None, description="ISO3 country code: NGA, BEN, TGO, GHA, CIV"),
    start_year: int = Query(None, description="Start year filter"),
    end_year: int = Query(None, description="End year filter"),
):
    """Return indicator time-series data for corridor countries."""
    return worldbank_service.get_indicator(indicator, country, start_year, end_year)


@router.get("/summary")
async def country_summary(
    country: str = Query(None, description="ISO3 country code: NGA, BEN, TGO, GHA, CIV"),
):
    """Return latest values for all indicators for a country (or all countries)."""
    return worldbank_service.get_country_summary(country)


@router.get("/livestock")
async def livestock(
    species: str = Query(None, description="Filter by species: cattle, goats, sheep, chickens, pigs"),
):
    """Return FAO livestock density statistics for the corridor."""
    return livestock_service.get_livestock(species)


@router.get("/connectivity")
async def connectivity(
    type: str = Query("mobile", description="Network type: mobile or fixed"),
):
    """Return Ookla Speedtest internet speed/coverage data."""
    return connectivity_service.get_connectivity(type)
