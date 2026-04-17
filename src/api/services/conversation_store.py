"""Conversation persistence — PostgreSQL-backed with in-memory fallback."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from src.api.config import DATABASE_URI, CONVERSATION_MAX_MESSAGES, CONVERSATION_TIMEOUT_MINUTES

logger = logging.getLogger("corridor.api.conversation_store")

# ── In-memory fallback (same as the original chat_service store) ─────────

_memory_store: dict[str, dict] = {}
_MAX_MEMORY_CONVERSATIONS = 10_000


def _mem_get(conversation_id: str) -> list[dict]:
    conv = _memory_store.get(conversation_id)
    if not conv:
        return []
    elapsed_min = (time.time() - conv["last_active"]) / 60
    if elapsed_min > CONVERSATION_TIMEOUT_MINUTES:
        del _memory_store[conversation_id]
        return []
    return conv["messages"][-CONVERSATION_MAX_MESSAGES:]


def _mem_save(conversation_id: str, messages: list[dict]) -> None:
    if len(_memory_store) >= _MAX_MEMORY_CONVERSATIONS and conversation_id not in _memory_store:
        # Evict oldest entry
        oldest = min(_memory_store, key=lambda k: _memory_store[k]["last_active"])
        del _memory_store[oldest]
    _memory_store[conversation_id] = {
        "messages": messages[-CONVERSATION_MAX_MESSAGES:],
        "last_active": time.time(),
    }


# ── PostgreSQL backend ──────────────────────────────────────────────────

_pool = None
_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS conversations (
    id         TEXT PRIMARY KEY,
    messages   JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


def _get_pool():
    """Lazily create a connection pool and ensure the table exists."""
    global _pool
    if _pool is not None:
        return _pool
    if not DATABASE_URI:
        return None
    try:
        from psycopg_pool import ConnectionPool
        _pool = ConnectionPool(conninfo=DATABASE_URI, min_size=1, max_size=5, timeout=5)
        with _pool.connection() as conn:
            conn.execute(_CREATE_TABLE)
        logger.info("Conversation store: PostgreSQL connected")
        return _pool
    except Exception as exc:
        logger.warning("Conversation store: PostgreSQL unavailable (%s), using in-memory", exc)
        return None


def _pg_get(conversation_id: str) -> list[dict]:
    pool = _get_pool()
    if pool is None:
        return _mem_get(conversation_id)
    try:
        with pool.connection() as conn:
            row = conn.execute(
                "SELECT messages, updated_at FROM conversations WHERE id = %s",
                (conversation_id,),
            ).fetchone()
        if not row:
            return []
        messages, updated_at = row
        elapsed_min = (time.time() - updated_at.timestamp()) / 60
        if elapsed_min > CONVERSATION_TIMEOUT_MINUTES:
            _pg_delete(conversation_id)
            return []
        if isinstance(messages, str):
            messages = json.loads(messages)
        return messages[-CONVERSATION_MAX_MESSAGES:]
    except Exception as exc:
        logger.warning("pg_get failed (%s), falling back to memory", exc)
        return _mem_get(conversation_id)


def _pg_save(conversation_id: str, messages: list[dict]) -> None:
    pool = _get_pool()
    if pool is None:
        return _mem_save(conversation_id, messages)
    trimmed = messages[-CONVERSATION_MAX_MESSAGES:]
    try:
        with pool.connection() as conn:
            conn.execute(
                """
                INSERT INTO conversations (id, messages, updated_at)
                VALUES (%s, %s::jsonb, now())
                ON CONFLICT (id) DO UPDATE
                    SET messages = EXCLUDED.messages,
                        updated_at = now()
                """,
                (conversation_id, json.dumps(trimmed)),
            )
    except Exception as exc:
        logger.warning("pg_save failed (%s), falling back to memory", exc)
        _mem_save(conversation_id, messages)


def _pg_delete(conversation_id: str) -> None:
    pool = _get_pool()
    if pool is None:
        _memory_store.pop(conversation_id, None)
        return
    try:
        with pool.connection() as conn:
            conn.execute("DELETE FROM conversations WHERE id = %s", (conversation_id,))
    except Exception:
        _memory_store.pop(conversation_id, None)


# ── Public API (auto-selects backend) ───────────────────────────────────

def get_conversation(conversation_id: str | None) -> list[dict]:
    """Get conversation history, clearing stale entries."""
    if not conversation_id:
        return []
    return _pg_get(conversation_id)


def save_conversation(conversation_id: str | None, messages: list[dict]) -> None:
    """Persist conversation messages."""
    if not conversation_id:
        return
    _pg_save(conversation_id, messages)


def is_db_reachable() -> bool:
    """Check if the PostgreSQL backend is reachable (for readiness probe)."""
    pool = _get_pool()
    if pool is None:
        return False
    try:
        with pool.connection() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:
        return False
