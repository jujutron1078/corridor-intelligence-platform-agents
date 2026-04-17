"""
Middleware that builds context from orchestrator agent state
and injects it so the agent prompt and model maintain context.
"""
from typing import Any, Callable

from langchain.agents.middleware import wrap_model_call
from langchain.agents.middleware.types import ModelRequest, ModelResponse


def build_context_from_state(state: dict[str, Any]) -> dict[str, str]:
    """
    Build context summaries from orchestrator agent state.
    """
    todos = state.get("todos", [])
    if not isinstance(todos, list):
        todos = []

    todo_parts = []
    for t in todos:
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


def _get_policy_context() -> str:
    """Load policy context for agent injection (cached after first call)."""
    try:
        from src.api.services import policy_service
        if policy_service.is_loaded():
            return policy_service.get_policy_context_for_agents()
    except Exception:
        pass
    return ""


def _get_data_availability() -> str:
    """Summarize what data is available so the agent knows what to query."""
    lines = ["## Available Corridor Data (use query_corridor_data to access)\n"]
    try:
        from src.api.services import worldbank_service, trade_service, energy_service
        from src.api.services import acled_service, projects_enriched_service

        # Projects
        try:
            ps = projects_enriched_service.get_summary()
            lines.append(f"- **Projects**: {ps.get('total_projects', 0)} corridor projects, "
                         f"${ps.get('total_cost_usd_million', 0)/1000:.0f}B pipeline")
        except Exception:
            pass

        # Energy
        try:
            from src.api.services import energy_service as es
            if es.is_loaded():
                plants = es.get_power_plants()
                n = len(plants.get("features", []))
                lines.append(f"- **Energy**: {n} power plants tracked")
        except Exception:
            pass

        # Conflict
        try:
            if acled_service.is_loaded():
                events = acled_service.get_conflict_events()
                total = events.get("summary", {}).get("total_events", 0)
                lines.append(f"- **Conflict**: {total} ACLED events")
        except Exception:
            pass

        # Trade
        lines.append("- **Trade**: 14 commodities (cocoa, gold, oil, rubber, cashew, palm_oil, cotton, fish, timber, bauxite, cement, phosphates, manganese, shea)")
        lines.append("- **Indicators**: GDP, GDP_GROWTH, FDI, TRADE_PCT_GDP, INFLATION, POPULATION, ELECTRICITY_ACCESS, INTERNET_USERS")
        lines.append("- **Policy**: 5 country investment policies + ECOWAS/AfCFTA frameworks + V-Dem governance")
        lines.append("- **Agriculture**: 14 crops across 5 countries (FAO data)")
        lines.append("- **Tourism**: 5 countries (arrivals, receipts, employment)")
        lines.append("- **Manufacturing**: 58 companies tracked")
        lines.append("- **Geospatial**: Nightlights, NDVI, Population, Landcover, Elevation, Protected Areas")
        lines.append("\n**Rule**: For ANY data question, call query_corridor_data FIRST. Do NOT give generic answers.")
    except Exception:
        pass
    return "\n".join(lines)


def _build_context_message(context: dict[str, str]) -> str:
    """Build a single context string for the injected user message."""
    parts = [
        "## Current session context (use when planning and answering)",
        "",
        "**Task list:**",
        context["todos_summary"],
    ]

    policy_ctx = _get_policy_context()
    if policy_ctx:
        parts.append("")
        parts.append(policy_ctx)

    data_ctx = _get_data_availability()
    if data_ctx:
        parts.append("")
        parts.append(data_ctx)

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

