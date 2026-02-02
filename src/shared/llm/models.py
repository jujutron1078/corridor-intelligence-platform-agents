from typing import Literal


SupportedLLM = Literal[
    "openai:gpt-5.1",
    "openai:gpt-5.2",
    # Google Gemini (use GOOGLE_API_KEY env)
    "google_genai:gemini-2.5-pro",
]

