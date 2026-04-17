"""
ACLED live API router — OAuth2 Bearer token auth via httpx.

Endpoints:
    GET /acled/health          — token status and API reachability
    GET /acled/events          — general-purpose event query
    GET /acled/events/country/{country}  — events by country
    GET /acled/events/region/{region}    — events by region
    GET /acled/events/fatalities         — fatal events filter
    GET /acled/events/summary           — count summary by event_type
"""

from __future__ import annotations

import logging
import time
from collections import Counter
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from src.api.services.acled_live import get_access_token, acled_get as _acled_get, _token_cache

logger = logging.getLogger("corridor.api.acled")

router = APIRouter(prefix="/acled", tags=["ACLED"])


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.get("/health")
async def acled_health():
    """Check ACLED token validity and API reachability."""
    try:
        token = await get_access_token()
        return {
            "status": "ok",
            "token_valid": True,
            "token_expires_at": _token_cache["expires_at"],
            "seconds_remaining": max(0, int(_token_cache["expires_at"] - time.time())),
        }
    except HTTPException as exc:
        return {
            "status": "error",
            "token_valid": False,
            "detail": exc.detail,
        }


@router.get("/events")
async def get_events(
    country: str | None = Query(None, description="Exact country name, e.g. Kenya"),
    region: str | None = Query(None, description="Region, e.g. Western Africa"),
    event_type: str | None = Query(None, description="Battles, Protests, Riots, etc."),
    disorder_type: str | None = Query(None, description="Political violence, Demonstrations, etc."),
    start_date: str | None = Query(None, description="Start date YYYY-MM-DD"),
    end_date: str | None = Query(None, description="End date YYYY-MM-DD"),
    limit: int = Query(100, ge=1, le=5000),
    page: int = Query(1, ge=1),
):
    """General-purpose ACLED event query with optional filters."""
    params: dict[str, Any] = {"limit": limit, "page": page}

    if country:
        params["country"] = country
    if region:
        params["region"] = region
    if event_type:
        params["event_type"] = event_type
    if disorder_type:
        params["disorder_type"] = disorder_type
    if start_date and end_date:
        params["event_date"] = f"{start_date}|{end_date}"
        params["event_date_where"] = "BETWEEN"
    elif start_date:
        params["event_date"] = start_date
    elif end_date:
        params["event_date"] = end_date

    return await _acled_get(params)


@router.get("/events/country/{country}")
async def get_events_by_country(
    country: str,
    start_date: str | None = Query(None, description="Start date YYYY-MM-DD"),
    end_date: str | None = Query(None, description="End date YYYY-MM-DD"),
    event_type: str | None = Query(None, description="Battles, Protests, Riots, etc."),
    limit: int = Query(100, ge=1, le=5000),
):
    """Get ACLED events for a specific country."""
    params: dict[str, Any] = {"country": country, "limit": limit}

    if event_type:
        params["event_type"] = event_type
    if start_date and end_date:
        params["event_date"] = f"{start_date}|{end_date}"
        params["event_date_where"] = "BETWEEN"
    elif start_date:
        params["event_date"] = start_date
    elif end_date:
        params["event_date"] = end_date

    return await _acled_get(params)


@router.get("/events/region/{region}")
async def get_events_by_region(
    region: str,
    start_date: str | None = Query(None, description="Start date YYYY-MM-DD"),
    end_date: str | None = Query(None, description="End date YYYY-MM-DD"),
    limit: int = Query(100, ge=1, le=5000),
):
    """Get ACLED events for a specific region."""
    params: dict[str, Any] = {"region": region, "limit": limit}

    if start_date and end_date:
        params["event_date"] = f"{start_date}|{end_date}"
        params["event_date_where"] = "BETWEEN"
    elif start_date:
        params["event_date"] = start_date
    elif end_date:
        params["event_date"] = end_date

    return await _acled_get(params)


@router.get("/events/fatalities")
async def get_fatal_events(
    country: str | None = Query(None, description="Exact country name"),
    min_fatalities: int = Query(1, ge=0, description="Minimum fatalities threshold"),
    start_date: str | None = Query(None, description="Start date YYYY-MM-DD"),
    end_date: str | None = Query(None, description="End date YYYY-MM-DD"),
    limit: int = Query(100, ge=1, le=5000),
):
    """Get ACLED events filtered by fatality count."""
    params: dict[str, Any] = {
        "fatalities": min_fatalities,
        "fatalities_where": ">=",
        "limit": limit,
    }

    if country:
        params["country"] = country
    if start_date and end_date:
        params["event_date"] = f"{start_date}|{end_date}"
        params["event_date_where"] = "BETWEEN"
    elif start_date:
        params["event_date"] = start_date
    elif end_date:
        params["event_date"] = end_date

    return await _acled_get(params)


@router.get("/events/summary")
async def get_events_summary(
    country: str | None = Query(None, description="Exact country name"),
    region: str | None = Query(None, description="Region, e.g. Western Africa"),
    start_date: str | None = Query(None, description="Start date YYYY-MM-DD"),
    end_date: str | None = Query(None, description="End date YYYY-MM-DD"),
):
    """Fetch recent events and return count summary grouped by event_type."""
    params: dict[str, Any] = {"limit": 5000}

    if country:
        params["country"] = country
    if region:
        params["region"] = region
    if start_date and end_date:
        params["event_date"] = f"{start_date}|{end_date}"
        params["event_date_where"] = "BETWEEN"
    elif start_date:
        params["event_date"] = start_date
    elif end_date:
        params["event_date"] = end_date

    data = await _acled_get(params)
    events = data.get("data", [])

    counts = Counter(evt.get("event_type", "Unknown") for evt in events)
    total_fatalities = sum(int(evt.get("fatalities", 0)) for evt in events)

    return {
        "total_events": len(events),
        "total_fatalities": total_fatalities,
        "by_event_type": dict(counts),
    }
