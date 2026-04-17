"""
Middleware that trims large tool-message content before LLM calls.

Prevents context-window overflow when agents execute multi-tool chains
that produce large GeoJSON payloads, coordinate arrays, or detection
catalogues.  The trimmed version is only seen by the LLM — the original
ToolMessage stored in agent state (and forwarded to the frontend) is
untouched.
"""

import json
import logging
from typing import Any

from langchain.agents.middleware import wrap_model_call
from langchain.agents.middleware.types import ModelRequest, ModelResponse
from langchain_core.messages import AIMessage, ToolMessage

logger = logging.getLogger("corridor.middleware.trim_context")

# ── Tunables ─────────────────────────────────────────────────────────────────
MAX_TOOL_CONTENT_CHARS = 6_000   # trim tool messages larger than this
MAX_ARRAY_ITEMS = 12             # keep at most N items in any array
MAX_COORD_RING_POINTS = 8        # keep at most N coordinate pairs per ring
COORD_PRECISION = 4              # decimal places for coordinates
MAX_STRING_LEN = 500             # truncate individual string values


# ── JSON truncation helpers ──────────────────────────────────────────────────

def _is_coord_pair(value: Any) -> bool:
    """Check if value looks like a [lon, lat] coordinate pair."""
    return (
        isinstance(value, (list, tuple))
        and len(value) >= 2
        and all(isinstance(v, (int, float)) for v in value[:2])
    )


def _truncate_coord_ring(ring: list) -> list:
    """Truncate a coordinate ring, keeping first/last + sample."""
    if len(ring) <= MAX_COORD_RING_POINTS:
        return [[round(c, COORD_PRECISION) if isinstance(c, (int, float)) else c for c in pair] for pair in ring]

    kept = ring[:4] + ring[-2:]
    result = [[round(c, COORD_PRECISION) if isinstance(c, (int, float)) else c for c in pair] for pair in kept]
    result.append(f"...{len(ring)} coords total, truncated for LLM context")
    return result


def _truncate_value(value: Any, depth: int = 0) -> Any:
    """Recursively truncate a JSON value to reduce token count."""
    if depth > 8:
        if isinstance(value, str) and len(value) > 100:
            return value[:100] + "..."
        return value

    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for k, v in value.items():
            if k == "coordinates" and isinstance(v, list):
                # GeoJSON coordinates — special handling
                out[k] = _truncate_coordinates(v)
            else:
                out[k] = _truncate_value(v, depth + 1)
        return out

    if isinstance(value, list):
        # Check if this is a coordinate ring (list of [lon, lat])
        if len(value) > 0 and _is_coord_pair(value[0]):
            return _truncate_coord_ring(value)

        # Generic array truncation
        if len(value) > MAX_ARRAY_ITEMS:
            truncated = [_truncate_value(item, depth + 1) for item in value[:MAX_ARRAY_ITEMS]]
            truncated.append(f"...{len(value)} items total, showing first {MAX_ARRAY_ITEMS}")
            return truncated
        return [_truncate_value(item, depth + 1) for item in value]

    if isinstance(value, float):
        return round(value, COORD_PRECISION)

    if isinstance(value, str) and len(value) > MAX_STRING_LEN:
        return value[:MAX_STRING_LEN] + f"... [{len(value)} chars]"

    return value


def _truncate_coordinates(coords: list) -> list:
    """Handle GeoJSON coordinates at any nesting level."""
    if not coords:
        return coords

    # MultiPolygon: [[[[lon,lat], ...], ...], ...]  (list of polygons)
    if (
        isinstance(coords[0], list)
        and len(coords[0]) > 0
        and isinstance(coords[0][0], list)
        and len(coords[0][0]) > 0
        and isinstance(coords[0][0][0], list)
    ):
        return [[_truncate_coord_ring(ring) for ring in polygon] for polygon in coords]

    # Polygon: [[[lon,lat], ...], ...]  (list of rings)
    if (
        isinstance(coords[0], list)
        and len(coords[0]) > 0
        and isinstance(coords[0][0], list)
    ):
        return [_truncate_coord_ring(ring) for ring in coords]

    # LineString / single ring: [[lon,lat], ...]
    if isinstance(coords[0], (list, tuple)) and len(coords[0]) >= 2:
        return _truncate_coord_ring(coords)

    return coords


def _trim_content(content: str) -> str:
    """Trim a large JSON tool-message content string."""
    try:
        data = json.loads(content)
    except (json.JSONDecodeError, TypeError):
        # Not JSON — hard-truncate
        return content[:MAX_TOOL_CONTENT_CHARS] + "... [truncated]"

    truncated = _truncate_value(data)
    result = json.dumps(truncated, separators=(",", ":"))

    # Safety: if still too large after structured truncation, hard-cut
    if len(result) > MAX_TOOL_CONTENT_CHARS * 2:
        result = result[:MAX_TOOL_CONTENT_CHARS] + "...[truncated]"

    return result


# ── Orphaned tool-call repair ─────────────────────────────────────────────────

def _repair_orphaned_tool_calls(messages: list) -> tuple[list, bool]:
    """
    If an AIMessage has tool_calls but some/all lack a matching ToolMessage
    response, inject synthetic error ToolMessages so the LLM doesn't reject
    the history.  This happens when a prior run crashed mid-tool-execution.
    """
    # Collect all tool_call_ids that have a response
    responded_ids: set[str] = set()
    for msg in messages:
        if isinstance(msg, ToolMessage):
            responded_ids.add(msg.tool_call_id)
        elif isinstance(msg, dict) and msg.get("role") == "tool":
            tc_id = msg.get("tool_call_id")
            if tc_id:
                responded_ids.add(tc_id)

    # Find orphaned tool_call_ids and inject synthetic responses
    repaired_messages: list = []
    repaired = False
    for msg in messages:
        repaired_messages.append(msg)

        # Extract tool_calls from AIMessage
        tool_calls: list | None = None
        if isinstance(msg, AIMessage) and msg.tool_calls:
            tool_calls = msg.tool_calls
        elif isinstance(msg, dict) and msg.get("role") == "assistant":
            tool_calls = msg.get("tool_calls")

        if tool_calls:
            for tc in tool_calls:
                tc_id = tc.get("id") if isinstance(tc, dict) else getattr(tc, "id", None)
                if tc_id and tc_id not in responded_ids:
                    tc_name = tc.get("name", "unknown") if isinstance(tc, dict) else getattr(tc, "name", "unknown")
                    logger.warning("Injecting synthetic tool response for orphaned call %s (%s)", tc_id, tc_name)
                    repaired_messages.append(
                        ToolMessage(
                            content=f"[Error: previous tool execution for '{tc_name}' failed due to an internal error]",
                            tool_call_id=tc_id,
                            name=tc_name,
                        )
                    )
                    responded_ids.add(tc_id)
                    repaired = True

    return repaired_messages, repaired


# ── Middleware ───────────────────────────────────────────────────────────────

@wrap_model_call
async def trim_tool_messages(
    request: ModelRequest,
    handler,
) -> ModelResponse:
    """
    Scan request.messages for large ToolMessages and replace their content
    with a trimmed version so the LLM stays within its context window.
    """
    messages = getattr(request, "messages", None) or []
    messages, repaired = _repair_orphaned_tool_calls(messages)
    new_messages = []
    changed = repaired

    for msg in messages:
        # Detect tool messages — handle both ToolMessage objects and dicts
        content: str | None = None
        is_tool = False

        if isinstance(msg, ToolMessage):
            is_tool = True
            content = msg.content if isinstance(msg.content, str) else None
        elif isinstance(msg, dict) and msg.get("role") == "tool":
            is_tool = True
            raw = msg.get("content")
            content = raw if isinstance(raw, str) else None

        if is_tool and content and len(content) > MAX_TOOL_CONTENT_CHARS:
            trimmed = _trim_content(content)
            logger.info(
                "Trimmed tool message from %d → %d chars (%.0f%% reduction)",
                len(content),
                len(trimmed),
                (1 - len(trimmed) / len(content)) * 100,
            )
            if isinstance(msg, ToolMessage):
                msg = ToolMessage(
                    content=trimmed,
                    tool_call_id=msg.tool_call_id,
                    name=msg.name,
                )
            else:
                msg = {**msg, "content": trimmed}
            changed = True

        new_messages.append(msg)

    if changed and hasattr(request, "override"):
        request = request.override(messages=new_messages)

    return await handler(request)
