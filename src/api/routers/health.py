"""
Health and meta endpoints.

GET /api/health, /api/usage
"""

from __future__ import annotations

from fastapi import APIRouter

from src.api.cache import gee_cache
from src.api.config import MODEL_ROUTES
from src.api.models.responses import HealthResponse, UsageResponse
from src.api.services import gee_service, osm_service, mineral_service, trade_service
from src.api.services.llm_service import is_connected as llm_connected, get_usage
from src.pipelines.gee_pipeline.config import DATASET_CATALOG

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health():
    """Return platform health status."""
    from src.shared.pipeline.freshness import get_freshness_report
    from src.api.config import SCHEDULER_ENABLED

    scheduler_status: dict = {"enabled": SCHEDULER_ENABLED, "running": False, "jobs": []}
    if SCHEDULER_ENABLED:
        try:
            from src.scheduler.scheduler import data_scheduler
            scheduler_status = data_scheduler.get_status()
        except Exception:
            pass

    return HealthResponse(
        status="ok",
        gee_connected=gee_service._api is not None,
        datasets_loaded=len(DATASET_CATALOG),
        osm_loaded=osm_service.is_loaded(),
        llm_connected=llm_connected(),
        model_routes={k: v["model"] for k, v in MODEL_ROUTES.items()},
        cache_stats=gee_cache.stats,
        data_freshness=get_freshness_report(),
        scheduler=scheduler_status,
    )


@router.get("/healthz/live", status_code=200)
async def liveness():
    """Liveness probe — always 200 if the process is running."""
    return {"status": "alive"}


@router.get("/healthz/ready", status_code=200)
async def readiness():
    """Readiness probe — 200 if core services are loaded (DB is optional)."""
    from fastapi.responses import JSONResponse
    from src.api.services.conversation_store import is_db_reachable

    services_ok = gee_service._api is not None or osm_service.is_loaded()
    db_ok = is_db_reachable()

    ready = services_ok  # DB is optional — in-memory fallbacks exist
    body = {"status": "ready" if ready else "not_ready", "services": services_ok, "database": db_ok}
    return JSONResponse(content=body, status_code=200 if ready else 503)


@router.get("/usage", response_model=UsageResponse)
async def usage():
    """Return LLM usage statistics (in-memory, resets on restart)."""
    data = get_usage()
    return UsageResponse(
        total_queries=data["total_queries"],
        total_cost_usd=data["total_cost_usd"],
        by_route=data["by_route"],
    )
