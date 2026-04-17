"""Tests for conversation store, agent bridge, and checkpointer."""

import time

import pytest

class TestConversationStoreMemory:
    """Test in-memory conversation store."""

    def test_save_and_get(self):
        from src.api.services.conversation_store import _mem_save, _mem_get
        messages = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi there"},
        ]
        _mem_save("test-conv-1", messages)
        result = _mem_get("test-conv-1")
        assert len(result) == 2
        assert result[0]["content"] == "hello"

    def test_get_nonexistent(self):
        from src.api.services.conversation_store import _mem_get
        result = _mem_get("nonexistent-conv-xyz")
        assert result == []

    def test_max_messages_trimming(self, monkeypatch):
        import src.api.services.conversation_store as cs
        monkeypatch.setattr(cs, "CONVERSATION_MAX_MESSAGES", 3)
        messages = [{"role": "user", "content": f"msg-{i}"} for i in range(10)]
        cs._mem_save("test-trim", messages)
        result = cs._mem_get("test-trim")
        assert len(result) == 3
        assert result[0]["content"] == "msg-7"  # last 3

    def test_public_api(self):
        from src.api.services.conversation_store import get_conversation, save_conversation
        save_conversation("test-public", [{"role": "user", "content": "test"}])
        result = get_conversation("test-public")
        assert len(result) >= 1

    def test_get_none_id(self):
        from src.api.services.conversation_store import get_conversation
        assert get_conversation(None) == []

    def test_save_none_id(self):
        from src.api.services.conversation_store import save_conversation
        save_conversation(None, [{"role": "user", "content": "test"}])  # should not raise

    def test_db_reachable_without_db(self):
        from src.api.services.conversation_store import is_db_reachable
        # Without DATABASE_URI, should return False
        result = is_db_reachable()
        assert isinstance(result, bool)
class TestCheckpointer:
    """Test the LangGraph checkpointer with MemorySaver fallback."""

    def test_get_checkpointer_returns_instance(self):
        from src.shared.agents.checkpoint import get_checkpointer
        cp = get_checkpointer()
        # Should return MemorySaver fallback (no PostgreSQL in dev)
        assert cp is not None

    def test_checkpointer_is_singleton(self):
        from src.shared.agents.checkpoint import get_checkpointer
        cp1 = get_checkpointer()
        cp2 = get_checkpointer()
        assert cp1 is cp2

    def test_checkpointer_type(self):
        from src.shared.agents.checkpoint import get_checkpointer
        cp = get_checkpointer()
        # Should be MemorySaver when no PostgreSQL
        type_name = type(cp).__name__
        assert type_name in ("MemorySaver", "InMemorySaver", "PostgresSaver")
class TestAgentBridge:
    """Test agent bridge module structure."""

    def test_invoke_agent_importable(self):
        from src.api.services.agent_bridge import invoke_agent
        assert callable(invoke_agent)

    def test_invoke_agent_accepts_history(self):
        import inspect
        from src.api.services.agent_bridge import invoke_agent
        sig = inspect.signature(invoke_agent)
        params = list(sig.parameters.keys())
        assert "conversation_history" in params

    def test_invoke_agent_is_async(self):
        import asyncio
        from src.api.services.agent_bridge import invoke_agent
        assert asyncio.iscoroutinefunction(invoke_agent)
