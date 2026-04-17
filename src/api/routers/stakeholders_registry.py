"""
Stakeholders registry endpoints.

GET /api/stakeholders-registry/stakeholders, /api/stakeholders-registry/summary
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from src.api.services import stakeholders_registry_service

router = APIRouter(prefix="/api/stakeholders-registry", tags=["stakeholders-registry"])


@router.get("/stakeholders")
async def stakeholders(
    country: str = Query(None, description="ISO3 country code: NGA, BEN, TGO, GHA, CIV"),
    org_type: str = Query(None, description="Filter by organisation type"),
    sector: str = Query(None, description="Filter by sector"),
):
    """Return stakeholders filtered by country, organisation type, and sector."""
    return stakeholders_registry_service.get_stakeholders(country, org_type, sector)


@router.get("/summary")
async def summary():
    """Return a summary of stakeholders across all countries."""
    return stakeholders_registry_service.get_summary()
