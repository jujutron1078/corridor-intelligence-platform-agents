"""Shared pytest fixtures for the Corridor Intelligence Platform test suite."""

import sys
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def mock_runtime():
    """Create a mock ToolRuntime with a tool_call_id."""
    rt = MagicMock()
    rt.tool_call_id = "test-call-001"
    return rt


@pytest.fixture
def api_client():
    """Create a FastAPI TestClient."""
    from fastapi.testclient import TestClient
    from src.api.main import app
    return TestClient(app)


def extract_tool_response(command) -> dict:
    """Extract JSON response from a Command's ToolMessage."""
    messages = command.update["messages"]
    assert len(messages) == 1
    return json.loads(messages[0].content)
