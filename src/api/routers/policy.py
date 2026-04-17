"""
Policy & governance endpoints.

GET /api/policy/*
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from src.api.services import policy_service

router = APIRouter(prefix="/api/policy", tags=["policy"])


@router.get("/policies")
async def policies(
    country: str = Query(None, description="ISO3 code: NGA, BEN, TGO, GHA, CIV"),
    category: str = Query(None, description="Category: investment, environment, trade"),
):
    """Return policy data, optionally filtered by country and category."""
    return policy_service.get_policies(country, category)


@router.get("/comparison")
async def comparison():
    """Cross-country policy comparison for key investment metrics."""
    return policy_service.get_comparison()


@router.get("/governance")
async def governance():
    """V-Dem governance indicators for all corridor countries."""
    return policy_service.get_governance()
