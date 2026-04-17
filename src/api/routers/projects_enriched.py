"""
Projects enriched endpoints.

GET /api/projects-enriched/projects, /api/projects-enriched/timeline,
GET /api/projects-enriched/summary
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from src.api.services import projects_enriched_service

router = APIRouter(prefix="/api/projects-enriched", tags=["projects-enriched"])


@router.get("/projects")
async def projects(
    country: str = Query(None, description="ISO3 country code: NGA, BEN, TGO, GHA, CIV"),
    sector: str = Query(None, description="Filter by project sector"),
    status: str = Query(None, description="Filter by project status"),
):
    """Return enriched project data filtered by country, sector, and status."""
    return projects_enriched_service.get_projects(country, sector, status)


@router.get("/timeline")
async def timeline():
    """Return a timeline view of projects across all countries."""
    return projects_enriched_service.get_timeline()


@router.get("/geojson")
async def projects_geojson():
    """Return all projects as GeoJSON for map rendering with sector icons and status."""
    return projects_enriched_service.get_geojson()


@router.get("/summary")
async def summary():
    """Return an enriched summary of projects across all countries."""
    return projects_enriched_service.get_summary()
