"""Tests for LLM selector, model routing, and API config."""
import pytest

class TestLLMSelector:
    """Test the LLM factory and model selection."""

    def test_make_llm_returns_model(self):
        from src.shared.agents.llm.llm_selector import make_llm
        llm = make_llm("gpt-4o")
        assert llm is not None

    def test_make_llm_with_temperature(self):
        from src.shared.agents.llm.llm_selector import make_llm
        llm = make_llm("gpt-4o", temperature=0.5)
        assert llm is not None

    def test_default_llm_exists(self):
        from src.shared.agents.llm.llm_selector import default_llm
        assert default_llm is not None

    def test_openai_model_map(self):
        from src.shared.agents.llm.llm_selector import _OPENAI_MODEL_MAP
        assert "gpt-4o" in _OPENAI_MODEL_MAP
        assert "gpt-4o-mini" in _OPENAI_MODEL_MAP
        # Legacy Gemini IDs should map to OpenAI equivalents
        assert "google/gemini-2.5-flash" in _OPENAI_MODEL_MAP

    def test_make_openai_llm_returns_chatopenai(self):
        from src.api.config import OPENAI_API_KEY
        if not OPENAI_API_KEY:
            pytest.skip("No OPENAI_API_KEY")
        from src.shared.agents.llm.llm_selector import make_openai_llm
        llm = make_openai_llm("gpt-4o")
        assert "ChatOpenAI" in type(llm).__name__

    def test_make_openrouter_returns_chatopenai(self):
        from src.shared.agents.llm.llm_selector import make_openrouter_llm
        llm = make_openrouter_llm("openai/gpt-4o-mini")
        assert "ChatOpenAI" in type(llm).__name__

    def test_dynamic_model_selector_exists(self):
        from src.shared.agents.llm.llm_selector import dynamic_model_selector
        assert dynamic_model_selector is not None

    def test_openai_priority(self):
        """When OPENAI_API_KEY is set, make_llm should create an OpenAI instance."""
        from src.api.config import OPENAI_API_KEY
        if not OPENAI_API_KEY:
            pytest.skip("No OPENAI_API_KEY")
        from src.shared.agents.llm.llm_selector import make_llm
        llm = make_llm("gpt-4o")
        assert "ChatOpenAI" in type(llm).__name__

class TestModelRouting:
    """Test the API model routing configuration."""

    def test_6_routes(self):
        from src.api.config import MODEL_ROUTES
        assert len(MODEL_ROUTES) == 6

    def test_required_routes(self):
        from src.api.config import MODEL_ROUTES
        required = ["chat_agent", "synthesis", "bulk_nlp", "vision", "simple", "report"]
        for route in required:
            assert route in MODEL_ROUTES, f"Missing route: {route}"

    def test_route_structure(self):
        from src.api.config import MODEL_ROUTES
        for name, route in MODEL_ROUTES.items():
            assert "model" in route, f"{name} missing 'model'"
            assert "max_tokens" in route, f"{name} missing 'max_tokens'"
            assert "temperature" in route, f"{name} missing 'temperature'"
            assert "fallback" in route, f"{name} missing 'fallback'"
            assert "description" in route, f"{name} missing 'description'"

    def test_temperatures_valid(self):
        from src.api.config import MODEL_ROUTES
        for name, route in MODEL_ROUTES.items():
            t = route["temperature"]
            assert 0 <= t <= 1, f"{name} temperature {t} out of range"

    def test_agent_routing_config(self):
        from src.api.config import AGENT_ROUTING_ENABLED
        assert isinstance(AGENT_ROUTING_ENABLED, bool)
        # Should default to True after Phase 2 fix
        assert AGENT_ROUTING_ENABLED is True

    def test_openai_api_key_config(self):
        from src.api.config import OPENAI_API_KEY
        # Just check the config exists (may or may not be set)
        assert isinstance(OPENAI_API_KEY, str)

class TestAPIConfig:
    """Test API configuration values."""

    def test_cors_origins(self):
        from src.api.config import CORS_ORIGINS
        assert isinstance(CORS_ORIGINS, list)
        assert len(CORS_ORIGINS) >= 1

    def test_cache_settings(self):
        from src.api.config import CACHE_TTL_SECONDS, CACHE_TTL_STATIC, CACHE_MAX_SIZE
        assert CACHE_TTL_SECONDS > 0
        assert CACHE_TTL_STATIC == 86400
        assert CACHE_MAX_SIZE > 0

    def test_conversation_settings(self):
        from src.api.config import CONVERSATION_MAX_MESSAGES, CONVERSATION_TIMEOUT_MINUTES
        assert CONVERSATION_MAX_MESSAGES > 0
        assert CONVERSATION_TIMEOUT_MINUTES > 0

    def test_scheduler_config(self):
        from src.api.config import SCHEDULER_ENABLED
        assert isinstance(SCHEDULER_ENABLED, bool)
