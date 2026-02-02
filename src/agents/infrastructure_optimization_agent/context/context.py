from pydantic import BaseModel, Field
from typing import Literal

from src.shared.llm.models import SupportedLLM


class Context(BaseModel):
    user_name: str = Field(
        default="James Kanyiri",
        description="The name of the user",
    )
    user_role: str = Field(
        default="Senior AI Engineer",
        description="The role of the user in the organization",
    )
    user_email: str = Field(
        default="jkanyiri@bayesconsulting.co.ke",
        description="The email of the user",
    )
    user_phone: str = Field(
        default="+254797357665",
        description="The phone number of the user",
    )
    organization_name: Literal["bayes", "verst_carbon", "ignis_innovation", "afcen"] = (
        Field(
            default="bayes",
            description="The organization name. Determines which organization skill to load.",
        )
    )
    preferred_llm: SupportedLLM = Field(
        default="openai:gpt-5.2",
        description="The preferred LLM to use for the agent (all models support tool calling)",
    )
    llm_temperature: float = Field(
        default=0.0,
        description="Sampling temperature to use with the preferred LLM",
    )
