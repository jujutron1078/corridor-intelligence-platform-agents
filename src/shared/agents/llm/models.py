from typing import Literal


SupportedLLM = Literal[
    "gpt-4o",                                # Primary — tool calling, reasoning
    "gpt-4o-mini",                            # Lightweight — fast, cheap
    "gpt-4.1",                                # Latest flagship
    "gpt-4.1-mini",                           # Latest lightweight
    "o4-mini",                                # Reasoning model
    "anthropic/claude-sonnet-4",              # OpenRouter fallback
    "google/gemini-2.5-flash",                # OpenRouter fallback
]
