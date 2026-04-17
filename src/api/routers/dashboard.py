"""
Investor dashboard endpoints.

GET /api/dashboard/snapshot — composite payload for the Corridor Pulse dashboard.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Query

from src.api.models.dashboard import DashboardSnapshotResponse
from src.api.services import dashboard_service

logger = logging.getLogger("corridor.api.dashboard_router")

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/snapshot", response_model=DashboardSnapshotResponse)
async def dashboard_snapshot(year: int = Query(2023, ge=2012, le=2026)):
    """Return the full dashboard snapshot for a given year."""
    data = dashboard_service.get_snapshot(year)
    return DashboardSnapshotResponse(**data)
