"""
LLM gateway — model routing, provider fallback, cost tracking.

All LLM calls go through a single function that handles routing,
fallback, and error handling.  Provider priority: OpenAI → OpenRouter.
If the primary provider fails (quota, rate-limit, outage), the call
automatically falls through to the next available provider.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from src.api.config import (
    OPENAI_API_KEY, OPENAI_BASE_URL,
    OPENROUTER_API_KEY, OPENROUTER_BASE_URL,
    GEMINI_API_KEY,
    MODEL_ROUTES,
)

logger = logging.getLogger("corridor.api.llm_service")

# ── Usage tracking (in-memory, resets on restart) ────────────────────────────

_usage: dict[str, Any] = {
    "total_queries": 0,
    "total_cost_usd": 0.0,
    "by_route": {},
}


def get_usage() -> dict[str, Any]:
    """Return current usage statistics."""
    return dict(_usage)


def _track_usage(route: str, model: str, usage: dict) -> None:
    """Track a single LLM call's usage."""
    _usage["total_queries"] += 1

    prompt_tokens = usage.get("prompt_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)
    cost = usage.get("total_cost", 0)

    _usage["total_cost_usd"] += cost

    if route not in _usage["by_route"]:
        _usage["by_route"][route] = {
            "count": 0,
            "cost": 0.0,
            "total_prompt_tokens": 0,
            "total_completion_tokens": 0,
            "model": model,
        }

    _usage["by_route"][route]["count"] += 1
    _usage["by_route"][route]["cost"] += cost
    _usage["by_route"][route]["total_prompt_tokens"] += prompt_tokens
    _usage["by_route"][route]["total_completion_tokens"] += completion_tokens


def _get_provider_chain() -> list[tuple[str, str, dict]]:
    """Return a list of (base_url, api_key, extra_headers) for each configured provider."""
    providers = []
    if OPENAI_API_KEY:
        providers.append((OPENAI_BASE_URL, OPENAI_API_KEY, {}))
    if OPENROUTER_API_KEY:
        providers.append((
            OPENROUTER_BASE_URL,
            OPENROUTER_API_KEY,
            {
                "HTTP-Referer": "https://corridor-intelligence.dev",
                "X-Title": "Corridor Intelligence Platform",
            },
        ))
    if GEMINI_API_KEY:
        # Gemini via OpenAI-compatible endpoint through OpenRouter
        # (native Gemini is handled by llm_selector for agents)
        pass
    return providers


# ── Core LLM call ────────────────────────────────────────────────────────────

async def llm_call(
    route: str,
    messages: list[dict],
    tools: list[dict] | None = None,
    system: str | None = None,
    override_model: str | None = None,
) -> dict:
    """
    Unified LLM call with automatic routing and provider fallback.

    Priority: OpenAI API → OpenRouter → raise.

    If the primary provider fails (429 quota, rate-limit, 5xx, timeout),
    the call automatically falls through to the next provider.
    """
    config = MODEL_ROUTES[route]
    model = override_model or config["model"]

    all_messages = list(messages)
    if system:
        all_messages = [{"role": "system", "content": system}] + all_messages

    payload: dict[str, Any] = {
        "model": model,
        "messages": all_messages,
        "max_tokens": config["max_tokens"],
        "temperature": config["temperature"],
    }

    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    providers = _get_provider_chain()
    if not providers:
        raise RuntimeError("No LLM API keys configured (set OPENAI_API_KEY or OPENROUTER_API_KEY).")

    last_error: Exception | None = None

    async with httpx.AsyncClient(timeout=60.0) as client:
        for i, (base_url, api_key, extra_headers) in enumerate(providers):
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                **extra_headers,
            }

            try:
                logger.info("LLM call: route=%s model=%s api=%s", route, model, base_url)
                resp = await client.post(
                    f"{base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                )
                resp.raise_for_status()
                result = resp.json()

                usage_info = result.get("usage", {})
                _track_usage(route, model, usage_info)
                logger.info(
                    "LLM response: model=%s tokens=%d+%d",
                    model,
                    usage_info.get("prompt_tokens", 0),
                    usage_info.get("completion_tokens", 0),
                )
                return result

            except (httpx.HTTPStatusError, httpx.TimeoutException) as exc:
                last_error = exc
                remaining = len(providers) - i - 1
                logger.warning(
                    "LLM call failed (provider=%s model=%s): %s — %d provider(s) remaining",
                    base_url, model, exc, remaining,
                )
                # Try next provider
                continue

    # All providers exhausted — try fallback model on last provider as final attempt
    if config.get("fallback") and not override_model:
        fallback_model = config["fallback"]
        base_url, api_key, extra_headers = providers[-1]
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            **extra_headers,
        }
        payload["model"] = fallback_model

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                logger.info("Final fallback: model=%s api=%s", fallback_model, base_url)
                resp = await client.post(
                    f"{base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                )
                resp.raise_for_status()
                result = resp.json()

                usage_info = result.get("usage", {})
                _track_usage(route, fallback_model, usage_info)
                return result

            except Exception as fallback_exc:
                logger.error("Final fallback also failed: %s", fallback_exc)
                raise fallback_exc from last_error

    raise last_error  # type: ignore[misc]


def is_connected() -> bool:
    """Check if an LLM API key is configured (OpenAI or OpenRouter)."""
    return bool(OPENAI_API_KEY or OPENROUTER_API_KEY or GEMINI_API_KEY)
