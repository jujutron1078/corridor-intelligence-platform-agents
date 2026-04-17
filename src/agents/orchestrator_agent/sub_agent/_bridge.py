"""Shared helper for sub-agent tool wrappers.

Forwards structured tool outputs from domain agents alongside the
AI synthesis so the frontend can extract map overlay data from
orchestrator queries.
"""

from __future__ import annotations

import json

from langchain_core.messages import ToolMessage
from langgraph.types import Command


def build_sub_agent_result(response: dict, tool_call_id: str) -> Command:
    """Build a Command that includes both synthesis and structured tool data."""
    tool_results: list[dict[str, str]] = []

    for msg in response.get("messages", []):
        if getattr(msg, "type", "") != "tool":
            continue
        name = getattr(msg, "name", None)
        raw = getattr(msg, "content", "")
        if not name or not isinstance(raw, str):
            continue
        try:
            json.loads(raw)  # validate it's JSON
            tool_results.append({"tool_name": name, "content": raw})
        except (json.JSONDecodeError, TypeError):
            pass

    # Extract the final AI message as synthesis text
    synthesis = ""
    for msg in reversed(response.get("messages", [])):
        msg_type = getattr(msg, "type", "")
        if msg_type in ("ai", "AIMessage"):
            content = getattr(msg, "content", "")
            if isinstance(content, str):
                synthesis = content
            elif isinstance(content, list):
                synthesis = " ".join(
                    block.get("text", "") if isinstance(block, dict) else str(block)
                    for block in content
                )
            break

    # If we have structured tool data, wrap it so frontend can extract map overlays
    if tool_results:
        result = json.dumps({"synthesis": synthesis, "tool_results": tool_results})
    else:
        result = synthesis

    return Command(
        update={"messages": [ToolMessage(content=result, tool_call_id=tool_call_id)]}
    )
