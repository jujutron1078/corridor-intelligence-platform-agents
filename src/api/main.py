"""
Unified FastAPI application — Corridor Intelligence Platform.

Merges pipeline data services (GEE, OSM, USGS, trade, etc.) with
LangGraph agent workspace CRUD into a single deployable.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import os

from slowapi.errors import RateLimitExceeded

from src.api.config import CORS_ORIGINS, SCHEDULER_ENABLED
from src.api.schemas import error_response
from src.api.security import ApiKeyMiddleware, limiter, rate_limit_handler
from src.shared.pipeline.utils import setup_logging

logger = logging.getLogger("corridor.api")


_SERVICE_NAMES = [
    "gee_service", "osm_service", "mineral_service", "trade_service",
    "worldbank_service", "acled_service", "energy_service",
    "livestock_service", "connectivity_service", "policy_service",
    "manufacturing_service", "stakeholders_registry_service",
    "tourism_service", "agriculture_enriched_service",
    "infrastructure_enriched_service", "macro_enriched_service",
    "projects_enriched_service",
    "geospatial_service",
]


def _init_services():
    """Initialize all pipeline services (load data from disk into memory)."""
    import importlib
    for svc_name in _SERVICE_NAMES:
        try:
            svc = importlib.import_module(f"src.api.services.{svc_name}")
            if hasattr(svc, 'init'):
                svc.init()
            logger.info("%s initialized", svc_name)
        except Exception as exc:
            logger.warning("%s failed to initialize: %s", svc_name, exc)


def _background_data_sync_then_init():
    """Download data from R2, THEN initialize services so they read real data."""
    import threading
    def _work():
        try:
            from entrypoint_sync import sync
            sync()
            logger.info("R2 sync done — now initializing services with real data...")
            _init_services()
            logger.info("Services re-initialized after data sync")
        except Exception as exc:
            logger.warning("Background data sync/init failed: %s", exc)
    t = threading.Thread(target=_work, daemon=True, name="r2-sync-then-init")
    t.start()
    return t


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    setup_logging()
    logger.info("Starting Corridor Intelligence Platform API...")

    from pathlib import Path
    from src.shared.pipeline.utils import DATA_DIR
    data_exists = (DATA_DIR / "freshness.json").exists()

    if data_exists:
        logger.info("Data found at %s — initializing services immediately", DATA_DIR)
        _init_services()
    else:
        logger.info("No data at %s — syncing from R2 in background, services will init after", DATA_DIR)
        _background_data_sync_then_init()

    # Pre-warm GEE cache
    try:
        from src.api.services import gee_service
        gee_service.prewarm_cache()
    except Exception as exc:
        logger.warning("Cache pre-warm failed: %s", exc)

    # Check for missing data directories
    from pathlib import Path
    from src.shared.pipeline.utils import DATA_DIR

    missing = []
    for name in ("osm", "mineral", "trade", "worldbank"):
        d = DATA_DIR / name
        if not d.exists() or not any(d.iterdir()):
            missing.append(f"data/{name}/")
    if missing:
        logger.warning(
            "No data found in: %s. Endpoints will return empty results. "
            "Run 'python run_all.py setup' to populate data.",
            ", ".join(missing),
        )

    # Check data freshness
    try:
        from src.shared.pipeline.freshness import get_stale_pipelines, age_days
        stale = get_stale_pipelines()
        if stale:
            ages = ", ".join(
                f"{p} ({age_days(p):.0f}d)" if age_days(p) is not None else f"{p} (never)"
                for p in stale
            )
            logger.warning(
                "Stale data detected: %s. "
                "Run 'python run_all.py refresh' to update only stale pipelines.",
                ages,
            )
        else:
            logger.info("All data pipelines are fresh")
    except Exception as exc:
        logger.debug("Freshness check skipped: %s", exc)

    # Start background data scheduler
    if SCHEDULER_ENABLED:
        from src.scheduler.scheduler import data_scheduler
        data_scheduler.start()
        logger.info("Background data scheduler started")

    logger.info("API startup complete")

    yield

    # Stop scheduler
    if SCHEDULER_ENABLED:
        from src.scheduler.scheduler import data_scheduler
        data_scheduler.stop()

    logger.info("API shutting down")


_enable_docs = os.getenv("ENABLE_DOCS", "true").lower() in ("true", "1", "yes")

app = FastAPI(
    title="Corridor Intelligence Platform",
    description="Lagos-Abidjan Economic Corridor — Data Pipelines, AI Agents & API",
    version="0.2.0",
    lifespan=lifespan,
    docs_url="/api/docs" if _enable_docs else None,
    redoc_url="/api/redoc" if _enable_docs else None,
    openapi_url="/api/openapi.json" if _enable_docs else None,
)

# Rate limit registration (must precede routers)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# API-key auth (no-op when BACKEND_API_KEY is unset — dev default)
app.add_middleware(ApiKeyMiddleware)

# CORS — tightened allow_methods/headers; * in CORS_ORIGINS should only be used in dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in CORS_ORIGINS if o.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "X-API-Key"],
)


# ── Exception handlers (from agents repo) ───────────────────────────────────

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Return standard error shape for HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(str(exc.detail)),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Return standard error shape for unhandled exceptions."""
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content=error_response("Internal server error"),
    )


# ── Pipeline routers ────────────────────────────────────────────────────────

from src.api.routers import corridor, chat, infrastructure, trade, health, indicators, energy, acled, policy, dashboard
from src.api.routers import (
    manufacturing, stakeholders_registry, tourism,
    agriculture_enriched, infrastructure_enriched, macro_enriched, projects_enriched,
    geospatial,
)

app.include_router(corridor.router)       # /api/corridor/*
app.include_router(chat.router)           # /api/chat
app.include_router(infrastructure.router) # /api/roads, /api/minerals, etc.
app.include_router(trade.router)          # /api/trade/*
app.include_router(health.router)         # /api/health
app.include_router(indicators.router)     # /api/indicators/*
app.include_router(energy.router)         # /api/energy/*
app.include_router(acled.router)          # /api/acled/*
app.include_router(policy.router)         # /api/policy/*
app.include_router(dashboard.router)      # /api/dashboard/*

# Corridor enriched data routers
app.include_router(manufacturing.router)           # /api/manufacturing/*
app.include_router(stakeholders_registry.router)   # /api/stakeholders-registry/*
app.include_router(tourism.router)                 # /api/tourism/*
app.include_router(agriculture_enriched.router)    # /api/agriculture-enriched/*
app.include_router(infrastructure_enriched.router) # /api/infrastructure-enriched/*
app.include_router(macro_enriched.router)          # /api/macro-enriched/*
app.include_router(projects_enriched.router)       # /api/projects-enriched/*
app.include_router(geospatial.router)              # /api/geo/*

# ── Workspace routers (from agents) ─────────────────────────────────────────

from src.api.features.projects import router as projects_router
from src.api.features.threads import router as threads_router
from src.api.features.opportunities import router as opportunities_router

app.include_router(projects_router, prefix="/workspace")
app.include_router(threads_router, prefix="/workspace")
app.include_router(opportunities_router, prefix="/workspace")


# ── Root endpoint ────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    """Root endpoint — platform info."""
    return {
        "name": "Corridor Intelligence Platform",
        "version": "0.2.0",
        "docs": "/api/docs",
        "health": "/api/health",
        "workspace": "/workspace/projects",
    }


@app.get("/api/admin/data-status")
async def data_status():
    """Diagnostic: check /data contents and R2 sync status."""
    import subprocess, shutil
    from pathlib import Path
    from src.shared.pipeline.utils import DATA_DIR

    data_path = Path(DATA_DIR)
    contents = []
    if data_path.exists():
        for item in sorted(data_path.iterdir()):
            if item.is_dir():
                file_count = sum(1 for _ in item.rglob("*") if _.is_file())
                size_mb = sum(f.stat().st_size for f in item.rglob("*") if f.is_file()) / 1e6
                contents.append({"name": item.name, "files": file_count, "size_mb": round(size_mb, 1)})
            else:
                contents.append({"name": item.name, "files": 1, "size_mb": round(item.stat().st_size / 1e6, 1)})

    rclone_ok = shutil.which("rclone") is not None
    r2_key = bool(os.environ.get("R2_ACCESS_KEY"))
    r2_secret = bool(os.environ.get("R2_SECRET_KEY"))
    r2_endpoint = bool(os.environ.get("R2_ENDPOINT"))
    freshness = (data_path / "freshness.json").exists()

    return {
        "data_dir": str(data_path),
        "data_dir_exists": data_path.exists(),
        "freshness_json_exists": freshness,
        "pipeline_dirs": contents,
        "total_items": len(contents),
        "rclone_installed": rclone_ok,
        "r2_credentials_set": {"access_key": r2_key, "secret_key": r2_secret, "endpoint": r2_endpoint},
    }


@app.post("/api/admin/trigger-sync")
async def trigger_sync():
    """Manually trigger R2 data sync + service re-init (background). Always forces full sync."""
    import threading
    def _do():
        try:
            from entrypoint_sync import sync
            sync(force=True)
            logger.info("Manual sync done — re-initializing services...")

            _init_services()
            logger.info("Services re-initialized after manual sync")
        except Exception as exc:
            logger.error("Manual sync failed: %s", exc, exc_info=True)
    t = threading.Thread(target=_do, daemon=True, name="manual-sync")
    t.start()
    return {"status": "sync started in background", "note": "Check /api/admin/data-status in a few minutes"}


@app.get("/api/admin/test-r2")
async def test_r2():
    """Test R2 connectivity via boto3 — returns actual errors."""
    import traceback

    try:
        access_key = os.environ.get("R2_ACCESS_KEY", "")
        secret_key = os.environ.get("R2_SECRET_KEY", "")
        endpoint = os.environ.get("R2_ENDPOINT", "")
        data_dir = os.environ.get("CORRIDOR_DATA_ROOT", "/data")

        if not all([access_key, secret_key, endpoint]):
            return {"error": "R2 credentials not set"}

        import boto3
        from botocore.config import Config

        s3 = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version="s3v4"),
            region_name="auto",
        )

        # List top-level "directories" under v1/data/
        resp = s3.list_objects_v2(Bucket="corridor-data", Prefix="v1/data/", Delimiter="/", MaxKeys=30)
        prefixes = [p["Prefix"] for p in resp.get("CommonPrefixes", [])]
        obj_count = resp.get("KeyCount", 0)

        # Check data_dir writability
        writable = True
        write_error = None
        try:
            test_file = os.path.join(data_dir, ".write_test")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
        except Exception as e:
            writable = False
            write_error = str(e)

        return {
            "r2_connected": True,
            "r2_dirs_found": len(prefixes),
            "r2_top_level": prefixes,
            "r2_objects_in_page": obj_count,
            "data_dir": data_dir,
            "data_dir_writable": writable,
            "write_error": write_error,
        }
    except Exception as exc:
        return {"error": str(exc), "traceback": traceback.format_exc()}
