"""
API configuration — merged settings for pipeline + agent services.
"""

from __future__ import annotations

import os
from src.shared.pipeline.utils import load_env

load_env()

# ── Server ───────────────────────────────────────────────────────────────────

API_HOST = os.environ.get("API_HOST", "0.0.0.0")
API_PORT = int(os.environ.get("API_PORT", "8000"))
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")

# ── API Auth ────────────────────────────────────────────────────────────────
# Set BACKEND_API_KEY in production to require an X-API-Key header on /api/*
# and /workspace/* routes. If empty, auth is disabled (dev only).
BACKEND_API_KEY = os.environ.get("BACKEND_API_KEY", "")
AUTH_EXEMPT_PATHS = {"/", "/api/healthz/live", "/api/healthz/ready", "/api/docs", "/api/redoc", "/api/openapi.json"}

# ── Rate limiting ───────────────────────────────────────────────────────────
RATE_LIMIT_CHAT = os.environ.get("RATE_LIMIT_CHAT", "20/minute")
RATE_LIMIT_DEFAULT = os.environ.get("RATE_LIMIT_DEFAULT", "120/minute")

# ── Pipeline API Keys ────────────────────────────────────────────────────────

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEE_PROJECT = os.environ.get("GEE_PROJECT", "")
COMTRADE_API_KEY = os.environ.get("COMTRADE_API_KEY", "")
ACLED_USERNAME = os.environ.get("ACLED_USERNAME", "")
ACLED_PASSWORD = os.environ.get("ACLED_PASSWORD", "")

# ── Agent API Keys ───────────────────────────────────────────────────────────

TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")

# ── Infrastructure ───────────────────────────────────────────────────────────

REDIS_URI = os.environ.get("REDIS_URI", "redis://localhost:6379")
DATABASE_URI = os.environ.get("DATABASE_URI", "")

# ── Scheduler ────────────────────────────────────────────────────────────

SCHEDULER_ENABLED = os.getenv("SCHEDULER_ENABLED", "true").lower() in ("true", "1", "yes")

# ── Agent Routing ───────────────────────────────────────────────────────

AGENT_ROUTING_ENABLED = os.getenv("AGENT_ROUTING_ENABLED", "true").lower() in ("true", "1", "yes")

# ── Cache ────────────────────────────────────────────────────────────────────

CACHE_TTL_SECONDS = int(os.environ.get("CACHE_TTL_SECONDS", "3600"))
CACHE_TTL_STATIC = 86400  # 24 hours for static layers
CACHE_MAX_SIZE = 500

# ── OpenAI ─────────────────────────────────────────────────────────────────

OPENAI_BASE_URL = "https://api.openai.com/v1"

# ── OpenRouter (fallback) ────────────────────────────────────────────────────

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# ── Model Routing ────────────────────────────────────────────────────────────

MODEL_ROUTES = {
    "chat_agent": {
        "model": os.environ.get("ROUTE_CHAT_AGENT", "gpt-4o"),
        "max_tokens": 4096,
        "temperature": 0.1,
        "description": "Query interpretation, tool selection, data synthesis",
        "fallback": "gpt-4o-mini",
    },
    "synthesis": {
        "model": os.environ.get("ROUTE_SYNTHESIS", "gpt-4o"),
        "max_tokens": 8192,
        "temperature": 0.2,
        "description": "Complex multi-source synthesis, investor reports",
        "fallback": "gpt-4o-mini",
    },
    "bulk_nlp": {
        "model": os.environ.get("ROUTE_BULK_NLP", "gpt-4o-mini"),
        "max_tokens": 4096,
        "temperature": 0.0,
        "description": "Policy doc parsing, entity extraction, batch processing",
        "fallback": "gpt-4o-mini",
    },
    "vision": {
        "model": os.environ.get("ROUTE_VISION", "gpt-4o"),
        "max_tokens": 2048,
        "temperature": 0.1,
        "description": "Satellite/street imagery interpretation",
        "fallback": "gpt-4o-mini",
    },
    "simple": {
        "model": os.environ.get("ROUTE_SIMPLE", "gpt-4o-mini"),
        "max_tokens": 2048,
        "temperature": 0.3,
        "description": "Simple Q&A, greetings, help text, formatting",
        "fallback": "gpt-4o-mini",
    },
    "report": {
        "model": os.environ.get("ROUTE_REPORT", "gpt-4o"),
        "max_tokens": 8192,
        "temperature": 0.3,
        "description": "Investment briefs, due diligence reports, stakeholder summaries",
        "fallback": "gpt-4o-mini",
    },
}

# ── Conversation ─────────────────────────────────────────────────────────────

CONVERSATION_MAX_MESSAGES = 10
CONVERSATION_TIMEOUT_MINUTES = 30
