"""
ACLED conflict data fetcher — geocoded political violence and protest events.

API docs: https://apidocs.acleddata.com/
Uses OAuth2 with ACLED_USERNAME + ACLED_PASSWORD from .env.
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any

import requests

from src.shared.pipeline.utils import DATA_DIR, ensure_dir, retry

logger = logging.getLogger("corridor.acled")

# ── Configuration ──────────────────────────────────────────────────────────

ACLED_TOKEN_URL = "https://acleddata.com/oauth/token"
ACLED_API_URL = "https://acleddata.com/api/acled/read"

CORRIDOR_COUNTRIES = ["Nigeria", "Benin", "Togo", "Ghana", "Ivory Coast"]
CORRIDOR_ISO = {"Nigeria": 566, "Benin": 204, "Togo": 768, "Ghana": 288, "Ivory Coast": 384}

EVENT_TYPES = [
    "Battles",
    "Explosions/Remote violence",
    "Violence against civilians",
    "Protests",
    "Riots",
    "Strategic developments",
]

ACLED_DATA_DIR = DATA_DIR / "acled"

# ── OAuth2 token cache ────────────────────────────────────────────────────

_token_cache: dict[str, Any] = {"access_token": None, "expires_at": 0}


def _get_access_token() -> str:
    """Get a valid ACLED OAuth2 access token (sync), refreshing if expired."""
    now = time.time()
    if _token_cache["access_token"] and now < _token_cache["expires_at"]:
        return _token_cache["access_token"]

    username = os.environ.get("ACLED_USERNAME", "")
    password = os.environ.get("ACLED_PASSWORD", "")
    if not username or not password:
        raise EnvironmentError(
            "ACLED_USERNAME and ACLED_PASSWORD must be set in .env. "
            "Register at https://developer.acleddata.com/."
        )

    resp = requests.post(
        ACLED_TOKEN_URL,
        data={
            "username": username,
            "password": password,
            "grant_type": "password",
            "client_id": "acled",
        },
        timeout=30,
    )
    if resp.status_code != 200:
        raise EnvironmentError(f"ACLED OAuth2 failed ({resp.status_code}): {resp.text}")

    data = resp.json()
    _token_cache["access_token"] = data["access_token"]
    _token_cache["expires_at"] = now + data["expires_in"] - 60
    logger.info("ACLED OAuth2 token acquired, expires in %ds", data["expires_in"])
    return _token_cache["access_token"]


# ── API fetch functions ──────────────────────────────────────────────────────

def fetch_events(
    year: int | None = None,
    country: str | None = None,
    event_type: str | None = None,
    limit: int = 5000,
) -> list[dict[str, Any]]:
    """
    Fetch ACLED conflict events for corridor countries.

    Args:
        year: Optional year filter
        country: Optional country name filter (defaults to all corridor countries)
        event_type: Optional event type filter (Battles, Protests, etc.)
        limit: Max records to fetch

    Returns list of event dicts with lat/lon, date, actors, fatalities.
    """
    token = _get_access_token()

    params: dict[str, Any] = {
        "limit": limit,
        "_format": "json",
    }

    # Filter by corridor countries (pipe-delimited)
    params["country"] = country or "|".join(CORRIDOR_COUNTRIES)

    if year:
        params["year"] = year
    if event_type:
        params["event_type"] = event_type

    def _do_fetch():
        resp = requests.get(
            ACLED_API_URL,
            params=params,
            headers={"Authorization": f"Bearer {token}"},
            timeout=60,
            )
        resp.raise_for_status()
        return resp.json()

    data = retry(_do_fetch, max_retries=3, backoff=2.0)

    if not data or not data.get("success", True):
        logger.warning("ACLED API returned error: %s", data.get("error", "unknown"))
        return []

    events = data.get("data", [])
    logger.info("Fetched %d ACLED events (year=%s)", len(events), year)
    return events


def fetch_all_corridor_events(
    start_year: int | None = None,
    end_year: int | None = None,
) -> list[dict[str, Any]]:
    """
    Fetch all conflict events for corridor countries.

    Defaults to the last 12 months (ACLED free-tier recency limit).
    If start_year/end_year are given, fetches that range instead.
    """
    if start_year is None and end_year is None:
        # Free-tier accounts are limited to last 12 months — fetch current year
        from datetime import date
        current_year = date.today().year
        years = [current_year - 1, current_year]
    else:
        s = start_year or 2024
        e = end_year or 2025
        years = list(range(s, e + 1))

    all_events = []
    for year in years:
        logger.info("Fetching ACLED events for %d...", year)
        try:
            events = fetch_events(year=year)
            all_events.extend(events)
            logger.info("  %d: %d events", year, len(events))
        except Exception as exc:
            logger.error("Failed to fetch ACLED %d: %s", year, exc)
    return all_events


# ── Conversion & persistence ──────────────────────────────────────────────

def events_to_geojson(events: list[dict]) -> dict:
    """Convert ACLED events to GeoJSON FeatureCollection."""
    features = []
    for evt in events:
        try:
            lon = float(evt.get("longitude", 0))
            lat = float(evt.get("latitude", 0))
            if lon == 0 and lat == 0:
                continue

            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": {
                    "event_id": evt.get("event_id_cnty", ""),
                    "event_date": evt.get("event_date", ""),
                    "year": int(evt.get("year", 0)),
                    "event_type": evt.get("event_type", ""),
                    "sub_event_type": evt.get("sub_event_type", ""),
                    "actor1": evt.get("actor1", ""),
                    "actor2": evt.get("actor2", ""),
                    "country": evt.get("country", ""),
                    "admin1": evt.get("admin1", ""),
                    "admin2": evt.get("admin2", ""),
                    "location": evt.get("location", ""),
                    "fatalities": int(evt.get("fatalities", 0)),
                    "notes": evt.get("notes", ""),
                },
            })
        except (ValueError, TypeError):
            continue

    return {"type": "FeatureCollection", "features": features}


def save_events(events: list[dict]) -> Path:
    """Save ACLED events as GeoJSON."""
    ensure_dir(ACLED_DATA_DIR)
    geojson = events_to_geojson(events)
    path = ACLED_DATA_DIR / "conflict_events.geojson"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False)
    logger.info("Saved ACLED events: %s (%d features)", path, len(geojson["features"]))
    return path


def load_events() -> dict:
    """Load cached ACLED events GeoJSON."""
    path = ACLED_DATA_DIR / "conflict_events.geojson"
    if not path.exists():
        return {"type": "FeatureCollection", "features": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
