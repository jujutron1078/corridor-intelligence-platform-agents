"""
API-key auth middleware and rate limiter.

Wire in main.py with:

    from src.api.security import ApiKeyMiddleware, limiter
    app.add_middleware(ApiKeyMiddleware)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)

Individual endpoints can opt into tighter limits with `@limiter.limit(...)`.
"""

from __future__ import annotations

import hmac
import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from src.api.config import AUTH_EXEMPT_PATHS, BACKEND_API_KEY, RATE_LIMIT_DEFAULT
from src.api.schemas import error_response

logger = logging.getLogger("corridor.api.security")


class ApiKeyMiddleware(BaseHTTPMiddleware):
    """Require X-API-Key header on every request except health/docs routes.

    Skipped entirely when BACKEND_API_KEY is empty — that path is dev-only.
    Uses hmac.compare_digest to avoid timing-based key leaks.
    """

    async def dispatch(self, request: Request, call_next):
        if not BACKEND_API_KEY:
            return await call_next(request)

        path = request.url.path
        if path in AUTH_EXEMPT_PATHS or path.startswith("/docs/oauth2-redirect"):
            return await call_next(request)

        presented = request.headers.get("x-api-key", "")
        if not presented or not hmac.compare_digest(presented, BACKEND_API_KEY):
            logger.warning("Rejected request to %s: missing/invalid API key", path)
            return JSONResponse(
                status_code=401,
                content=error_response("Missing or invalid API key"),
            )
        return await call_next(request)


def _client_key(request: Request) -> str:
    """Rate-limit key: prefer API key (per-tenant), fall back to IP (per-origin)."""
    api_key = request.headers.get("x-api-key")
    if api_key:
        return f"key:{api_key[:12]}"
    return f"ip:{get_remote_address(request)}"


limiter = Limiter(key_func=_client_key, default_limits=[RATE_LIMIT_DEFAULT])


async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content=error_response(f"Rate limit exceeded: {exc.detail}"),
    )
