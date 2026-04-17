"""
Shared ACLED live API client — OAuth2 token management and authenticated requests.

Used by both api/routers/acled.py and api/services/acled_service.py.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx
from fastapi import HTTPException

from src.api.config import ACLED_USERNAME, ACLED_PASSWORD

logger = logging.getLogger("corridor.api.acled_live")

# ── Constants ────────────────────────────────────────────────────────────────

ACLED_TOKEN_URL = "https://acleddata.com/oauth/token"
ACLED_API_URL = "https://acleddata.com/api/acled/read"

# ── Token cache ──────────────────────────────────────────────────────────────

_token_cache: dict[str, Any] = {
    "access_token": None,
    "expires_at": 0,
}


async def get_access_token() -> str:
    """Get a valid ACLED OAuth2 access token, refreshing if expired."""
    now = time.time()
    if _token_cache["access_token"] and now < _token_cache["expires_at"]:
        return _token_cache["access_token"]

    if not ACLED_USERNAME or not ACLED_PASSWORD:
        raise HTTPException(
            status_code=401,
            detail="ACLED_USERNAME and ACLED_PASSWORD must be set in .env",
        )

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                ACLED_TOKEN_URL,
                data={
                    "username": ACLED_USERNAME,
                    "password": ACLED_PASSWORD,
                    "grant_type": "password",
                    "client_id": "acled",
                },
            )
        if resp.status_code != 200:
            raise HTTPException(
                status_code=401,
                detail="Failed to authenticate with ACLED",
            )
        data = resp.json()
        _token_cache["access_token"] = data["access_token"]
        _token_cache["expires_at"] = now + data["expires_in"] - 60
        logger.info("ACLED OAuth2 token acquired, expires in %ds", data["expires_in"])
        return _token_cache["access_token"]
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=401,
            detail="Failed to authenticate with ACLED",
        )


async def acled_get(params: dict[str, Any]) -> dict:
    """Make an authenticated GET request to the ACLED API."""
    token = await get_access_token()
    params["_format"] = "json"

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                ACLED_API_URL,
                params=params,
                headers={"Authorization": f"Bearer {token}"},
            )
        if resp.status_code != 200:
            raise HTTPException(
                status_code=resp.status_code,
                detail=resp.text,
            )
        return resp.json()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail="ACLED API request failed")
