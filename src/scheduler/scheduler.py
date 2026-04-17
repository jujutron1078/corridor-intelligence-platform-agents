"""Background data scheduler - keeps pipeline data fresh automatically.

Uses APScheduler's BackgroundScheduler to run cron jobs that re-pull
stale pipelines and reload their in-memory services.  Schedules are
derived from STALENESS_THRESHOLDS at roughly half-threshold intervals
so data is refreshed well before it goes stale.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from apscheduler.schedulers.background import BackgroundScheduler

from src.scheduler.jobs import PIPELINE_JOBS
from src.shared.pipeline.freshness import is_stale, STALENESS_THRESHOLDS

logger = logging.getLogger("corridor.scheduler")

# PostgreSQL advisory lock ID - arbitrary 64-bit int unique to the scheduler
_ADVISORY_LOCK_ID = 7_239_401_001

# Cron schedules - each pipeline refreshes at roughly half its staleness
# threshold, offset by hour to avoid concurrent heavy pulls.
#   day_interval: how often (in days) the job fires
#   hour:         UTC hour offset so jobs don't overlap
_CRON_SCHEDULES: dict[str, dict[str, Any]] = {
    "acled":          {"day_interval": 3,  "hour": 0},   # threshold  7d
    "trade_prices":   {"day_interval": 14, "hour": 1},   # threshold 30d
    "osm":            {"day_interval": 14, "hour": 2},   # threshold 30d
    "worldbank":      {"day_interval": 45, "hour": 3},   # threshold 90d
    "trade_comtrade": {"day_interval": 45, "hour": 4},   # threshold 90d
    "energy":         {"day_interval": 90, "hour": 5},   # threshold 180d
    "mineral":        {"day_interval": 90, "hour": 6},   # threshold 180d
    "imf":            {"day_interval": 45, "hour": 7},   # threshold  90d
    "gem":            {"day_interval": 45, "hour": 8},   # threshold  90d
    "fao":            {"day_interval": 45, "hour": 9},   # threshold  90d
    "gdl":            {"day_interval": 90, "hour": 10},  # threshold 180d
    "aiddata":        {"day_interval": 90, "hour": 11},  # threshold 180d
    "unctad":         {"day_interval": 90, "hour": 12},  # threshold 180d
    "energydata":     {"day_interval": 90, "hour": 13},  # threshold 180d
    "ppi":            {"day_interval": 90, "hour": 14},  # threshold 180d
    "cpi":            {"day_interval": 180, "hour": 15},  # threshold 365d
    "vdem":           {"day_interval": 180, "hour": 16},  # threshold 365d
    "gadm":           {"day_interval": 180, "hour": 17},  # threshold 365d
    "wapp":           {"day_interval": 180, "hour": 18},  # threshold 365d
}


class DataScheduler:
    """Singleton-style background scheduler for pipeline data refresh."""

    def __init__(self) -> None:
        self._scheduler: BackgroundScheduler | None = None
        self._last_results: dict[str, dict[str, Any]] = {}
        self._running = False
        self._lock_conn = None  # holds the advisory-lock connection

    # ── Public API ───────────────────────────────────────────────────────

    def _try_acquire_lock(self) -> bool:
        """Attempt a PostgreSQL advisory lock so only one replica runs jobs."""
        from src.api.config import DATABASE_URI
        if not DATABASE_URI:
            return True  # no DB → single-instance, always acquire
        try:
            import psycopg
            conn = psycopg.connect(conninfo=DATABASE_URI, autocommit=True, connect_timeout=5)
            row = conn.execute(
                "SELECT pg_try_advisory_lock(%s)", (_ADVISORY_LOCK_ID,)
            ).fetchone()
            if row and row[0]:
                self._lock_conn = conn  # keep alive to hold the lock
                logger.info("Scheduler advisory lock acquired")
                return True
            else:
                conn.close()
                logger.info("Scheduler advisory lock held by another replica - standing by")
                return False
        except Exception as exc:
            logger.warning("Advisory lock check failed (%s), proceeding anyway", exc)
            return True

    def start(self) -> None:
        """Register all cron jobs and start the scheduler."""
        if self._running:
            logger.warning("Scheduler already running")
            return

        if not self._try_acquire_lock():
            return

        self._scheduler = BackgroundScheduler(
            job_defaults={"misfire_grace_time": 3600},
        )

        for pipeline, sched in _CRON_SCHEDULES.items():
            job_fn = PIPELINE_JOBS.get(pipeline)
            if not job_fn:
                continue
            self._scheduler.add_job(
                self._wrap(pipeline, job_fn),
                trigger="interval",
                days=sched["day_interval"],
                start_date=f"2025-01-01 {sched['hour']:02d}:00:00",
                id=f"refresh_{pipeline}",
                name=f"Refresh {pipeline}",
                replace_existing=True,
            )

        # One-shot startup job: refresh anything already stale
        self._scheduler.add_job(
            self.run_stale_now,
            trigger="date",  # runs once immediately
            id="startup_stale_check",
            name="Startup stale-data refresh",
            replace_existing=True,
        )

        self._scheduler.start()
        self._running = True
        logger.info(
            "Data scheduler started - %d cron jobs registered",
            len(_CRON_SCHEDULES),
        )

    def stop(self) -> None:
        """Shut down the scheduler (non-blocking) and release advisory lock."""
        if self._scheduler and self._running:
            self._scheduler.shutdown(wait=False)
            self._running = False
            logger.info("Data scheduler stopped")
        if self._lock_conn:
            try:
                self._lock_conn.close()
            except Exception:
                pass
            self._lock_conn = None

    def run_stale_now(self) -> list[dict[str, Any]]:
        """Immediately refresh any currently-stale pipelines."""
        stale = [p for p in STALENESS_THRESHOLDS if is_stale(p)]
        if not stale:
            logger.info("Startup check: all pipelines are fresh")
            return []

        logger.info("Refreshing %d stale pipeline(s): %s",
                     len(stale), ", ".join(stale))
        results = []
        for pipeline in stale:
            job_fn = PIPELINE_JOBS.get(pipeline)
            if job_fn:
                result = job_fn()
                self._last_results[pipeline] = {
                    **result,
                    "run_at": datetime.now(timezone.utc).isoformat(
                        timespec="seconds"),
                }
                results.append(result)
        return results

    def get_status(self) -> dict[str, Any]:
        """Return scheduler status for the health endpoint."""
        jobs = []
        if self._scheduler and self._running:
            for job in self._scheduler.get_jobs():
                if job.id == "startup_stale_check":
                    continue  # skip the one-shot job
                pipeline = job.id.removeprefix("refresh_")
                last = self._last_results.get(pipeline)
                jobs.append({
                    "pipeline": pipeline,
                    "next_run": (job.next_run_time.isoformat(
                        timespec="seconds") if job.next_run_time else None),
                    "interval_days": _CRON_SCHEDULES.get(
                        pipeline, {}).get("day_interval"),
                    "last_status": last,
                })

        return {
            "enabled": True,
            "running": self._running,
            "jobs": jobs,
        }

    # ── Internal ─────────────────────────────────────────────────────────

    def _wrap(self, pipeline: str, fn):
        """Return a wrapper that stores the result after each run."""
        def _job():
            result = fn()
            self._last_results[pipeline] = {
                **result,
                "run_at": datetime.now(timezone.utc).isoformat(
                    timespec="seconds"),
            }
        return _job


# Module-level singleton
data_scheduler = DataScheduler()
