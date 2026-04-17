from langchain.agents.middleware.types import ModelRequest
from langchain.agents.middleware import wrap_model_call, ModelResponse
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_openai import ChatOpenAI

from src.api.config import (
    OPENAI_API_KEY, OPENAI_BASE_URL,
    OPENROUTER_API_KEY, OPENROUTER_BASE_URL,
    GEMINI_API_KEY,
)

_OPENROUTER_HEADERS = {
    "HTTP-Referer": "https://corridor-intelligence.bayes.co.ke",
}

# ── OpenAI model name mapping ─────────────────────────────────────────────
# Context preferred_llm may use OpenRouter-style IDs; map to native OpenAI.
_OPENAI_MODEL_MAP = {
    "gpt-4o": "gpt-4o",
    "gpt-4o-mini": "gpt-4o-mini",
    "gpt-4.1": "gpt-4.1",
    "gpt-4.1-mini": "gpt-4.1-mini",
    "o4-mini": "o4-mini",
    # Map non-OpenAI IDs to best OpenAI equivalent
    "openai/gpt-4o": "gpt-4o",
    "openai/gpt-4o-mini": "gpt-4o-mini",
    "google/gemini-2.5-flash": "gpt-4o-mini",
    "google/gemini-2.0-flash": "gpt-4o-mini",
    "deepseek/deepseek-v3.2-20251201": "gpt-4o-mini",
    "anthropic/claude-sonnet-4": "gpt-4o",
    "anthropic/claude-opus-4": "gpt-4o",
    "meta-llama/llama-3.1-70b-instruct": "gpt-4o-mini",
}

# Rate limiter: smooths burst traffic to stay within OpenAI RPM quotas.
# Tier 1 = 500 RPM, Tier 2 = 5000 RPM, Tier 3+ = 10000 RPM.
# Default ~15 RPS (~900 RPM) is safe for Tier 2+; adjust for Tier 1.
_openai_rate_limiter = InMemoryRateLimiter(
    requests_per_second=15,
    check_every_n_seconds=0.1,
    max_bucket_size=20,
)


def make_openai_llm(model: str, temperature: float = 0.0) -> ChatOpenAI:
    """Create a ChatOpenAI instance using the OpenAI API directly."""
    openai_model = _OPENAI_MODEL_MAP.get(model, "gpt-4o-mini")
    return ChatOpenAI(
        model=openai_model,
        api_key=OPENAI_API_KEY,
        temperature=temperature,
        max_retries=2,
        timeout=120,
        rate_limiter=_openai_rate_limiter,
    )


def make_openrouter_llm(model: str, temperature: float = 0.0) -> ChatOpenAI:
    """Create a ChatOpenAI instance routed through OpenRouter (fallback)."""
    return ChatOpenAI(
        model=model,
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
        temperature=temperature,
        default_headers=_OPENROUTER_HEADERS,
    )


def make_gemini_llm(model: str, temperature: float = 0.0):
    """Create a ChatGoogleGenerativeAI instance (fallback)."""
    from langchain_google_genai import ChatGoogleGenerativeAI

    _GEMINI_MODEL_MAP = {
        "google/gemini-2.5-flash": "gemini-2.5-flash",
        "google/gemini-2.0-flash": "gemini-2.0-flash",
    }
    gemini_model = _GEMINI_MODEL_MAP.get(model, "gemini-2.0-flash")
    return ChatGoogleGenerativeAI(
        model=gemini_model,
        google_api_key=GEMINI_API_KEY,
        temperature=temperature,
        max_retries=6,
        timeout=120,
    )


def make_llm(model: str, temperature: float = 0.0):
    """Create an LLM with automatic fallback: OpenAI → OpenRouter → Gemini.

    Uses LangChain's ``with_fallbacks`` so that quota errors, rate limits,
    or provider outages on the primary automatically fall through to the
    next available provider.
    """
    providers = []
    if OPENAI_API_KEY:
        providers.append(make_openai_llm(model, temperature))
    if OPENROUTER_API_KEY:
        providers.append(make_openrouter_llm(model, temperature))
    if GEMINI_API_KEY:
        providers.append(make_gemini_llm(model, temperature))

    if not providers:
        return make_openai_llm(model, temperature)

    primary = providers[0]
    if len(providers) > 1:
        return primary.with_fallbacks(providers[1:])
    return primary


default_llm = make_llm("gpt-4o")


@wrap_model_call
async def dynamic_model_selector(request: ModelRequest, handler) -> ModelResponse:
    """
    Dynamic model selector — reads preferred_llm and llm_temperature
    from agent context and swaps in the appropriate model.
    """
    context = request.runtime.context
    preferred_llm = context.preferred_llm
    llm_temperature = context.llm_temperature

    request.model = make_llm(preferred_llm, temperature=llm_temperature)
    return await handler(request)
