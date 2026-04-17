"""
Energy infrastructure endpoints.

GET /api/energy/plants, /api/energy/grid
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from src.api.services import energy_service

router = APIRouter(prefix="/api/energy", tags=["energy"])


@router.get("/plants")
async def power_plants(
    fuel: str = Query(None, description="Filter by fuel: solar, wind, hydro, gas, oil, coal, biomass"),
    country: str = Query(None, description="ISO3 country code: NGA, BEN, TGO, GHA, CIV"),
    min_capacity_mw: float = Query(None, description="Minimum capacity in MW"),
):
    """Return GeoJSON of power plants with capacity and fuel type."""
    return energy_service.get_power_plants(fuel, country, min_capacity_mw)


@router.get("/grid")
async def grid():
    """Return GeoJSON of electricity transmission grid lines."""
    return energy_service.get_grid()
