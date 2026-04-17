"""LangGraph checkpoint persistence - PostgreSQL-backed with in-memory fallback."""

from __future__ import annotations

import logging
import os

from src.api.config import DATABASE_URI

logger = logging.getLogger("corridor.agents.checkpoint")

_checkpointer = None
_resolved = False


def get_checkpointer():
    """Return a PostgresSaver instance, or MemorySaver fallback if DB unavailable.

    When running under LangGraph API server (langgraph dev / deploy), return None
    so the platform handles persistence automatically.
    """
    global _checkpointer, _resolved
    if _resolved:
        return _checkpointer

    # LangGraph API server manages its own checkpointing
    import sys
    if "langgraph_api" in sys.modules or "langgraph_runtime_inmem" in sys.modules:
        logger.info("Running under LangGraph API - using platform checkpointer")
        _resolved = True
        return None

    # Try PostgreSQL first
    if DATABASE_URI:
        try:
            from langgraph.checkpoint.postgres import PostgresSaver
            _checkpointer = PostgresSaver(conn_string=DATABASE_URI)
            _checkpointer.setup()
            logger.info("LangGraph PostgresSaver checkpointer ready")
            return _checkpointer
        except Exception as exc:
            logger.warning("Failed to init PostgresSaver: %s", exc)

    # Fall back to in-memory checkpointer
    try:
        from langgraph.checkpoint.memory import MemorySaver
        _checkpointer = MemorySaver()
        _resolved = True
        logger.info("LangGraph MemorySaver checkpointer ready (in-memory, not persistent)")
        return _checkpointer
    except Exception as exc:
        logger.warning("Failed to init MemorySaver: %s", exc)
        _resolved = True
        return None
