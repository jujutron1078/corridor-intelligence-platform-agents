from pydantic import BaseModel, Field
from typing import Literal

from src.shared.llm.models import SupportedLLM


class Context(BaseModel):
    user_name: str = Field(
        default="James Kanyiri",
        description="The name of the user",
    )
    preferred_llm: SupportedLLM = Field(
        default="openai:gpt-5.2",
        description="The preferred LLM to use for the agent (all models support tool calling)",
    )
    organization_name: Literal["bayes", "verst_carbon", "ignis_innovation", "afcen"] = Field(
        default="bayes",
        description="The organization name to use for proposal writing. Determines which organization skill to load.",
    )
    
