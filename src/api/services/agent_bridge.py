"""Agent bridge — invokes the orchestrator agent and returns a ChatResponse."""

from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage

from src.api.models.responses import ChatResponse

logger = logging.getLogger("corridor.api.agent_bridge")


def _extract_text(content) -> str:
    """Extract plain text from message content (handles Gemini's list-of-parts format)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict) and part.get("type") == "text":
                parts.append(part["text"])
        return "\n".join(parts)
    return str(content)


async def invoke_agent(
    message: str,
    conversation_id: str | None = None,
    conversation_history: list[dict] | None = None,
) -> ChatResponse:
    """
    Send *message* to the orchestrator agent and translate the result
    into a standard ChatResponse.

    Args:
        message: The user's message.
        conversation_id: Thread ID for LangGraph checkpointer state.
        conversation_history: Prior conversation messages from the conversation
            store, so the agent has context even on first invocation.
    """
    from src.agents.orchestrator_agent.agent import agent  # lazy import
    from src.agents.orchestrator_agent.context.context import Context

    logger.info("Routing to orchestrator agent (conversation=%s)", conversation_id)

    config = {
        "configurable": {"thread_id": conversation_id or "default"},
        "recursion_limit": 100,
    }

    # Build message list — include recent conversation history for context
    messages = []
    if conversation_history:
        for msg in conversation_history[-6:]:  # last 3 exchanges
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            # Skip assistant messages — agent has its own state via checkpointer

    # Always append the current user message
    messages.append(HumanMessage(content=message))

    result = await agent.ainvoke(
        {"messages": messages},
        config=config,
        context=Context(),
    )

    # Extract the final AI message text
    result_messages = result.get("messages", [])
    response_text = ""
    for msg in reversed(result_messages):
        if hasattr(msg, "content") and msg.content:
            # Skip tool messages — find the final AI response
            msg_type = getattr(msg, "type", "")
            if msg_type in ("ai", "AIMessage", "") and not getattr(msg, "tool_call_id", None):
                response_text = _extract_text(msg.content)
                break

    if not response_text:
        # Fallback: take any message with content
        for msg in reversed(result_messages):
            if hasattr(msg, "content") and msg.content:
                response_text = _extract_text(msg.content)
                break

    logger.info("Orchestrator agent responded (%d chars)", len(response_text))

    return ChatResponse(
        response=response_text,
        sources=["agent:orchestrator"],
        model_used="orchestrator",
        conversation_id=conversation_id,
    )
