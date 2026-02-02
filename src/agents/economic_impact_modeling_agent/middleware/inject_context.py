"""
Middleware that builds context from economic impact modeling agent state
and injects it so the agent prompt and model maintain context.
"""
from langchain.agents.middleware import wrap_model_call
from langchain.agents.middleware.types import ModelRequest, ModelResponse
from typing import Any, Callable


def build_context_from_state(state: dict[str, Any]) -> dict[str, str]:
    """
    Build context summaries from economic impact modeling agent state.
    """
    todos = state.get("todos", [])
    if not isinstance(todos, list):
        todos = []

    todo_parts = []
    for i, t in enumerate(todos):
        if isinstance(t, dict):
            content = t.get("content", "?")
            status = t.get("status", "?")
            todo_parts.append(f"- [{status}] {content}")
        else:
            todo_parts.append(f"- {t!r}")

    todos_summary = "\n".join(todo_parts) if todo_parts else "No tasks yet."

    return {
        "todos_summary": todos_summary,
    }


def _build_context_message(context: dict[str, str]) -> str:
    """Build a single context string for the injected user message."""
    parts = [
        "## Current session context (use when planning and answering)",
        "",
        "**Task list:**",
        context["todos_summary"],
    ]
    return "\n".join(parts)


@wrap_model_call
async def inject_context(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    """
    Inject context from state before recent messages so the model maintains
    session context. Builds a context message and prepends it to request.messages;
    also attaches injected_context for the dynamic prompt.
    """
    state = getattr(request, "state", None) or {}
    context = build_context_from_state(state)
    request.injected_context = context  # type: ignore[attr-defined]

    context_content = _build_context_message(context)
    messages = getattr(request, "messages", None) or []
    messages = [
        {"role": "user", "content": context_content},
        *messages,
    ]
    if hasattr(request, "override"):
        request = request.override(messages=messages)  # type: ignore[attr-defined]

    return await handler(request)
