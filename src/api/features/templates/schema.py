"""Schema definitions for template endpoints."""

from pydantic import BaseModel, Field
from typing import Generic, TypeVar

T = TypeVar("T")


class GetTemplatesRequest(BaseModel):
    """Request model for getting templates by agent name."""

    agent_name: str = Field(
        ...,
        description="The name of the agent to get templates for (e.g., 'grant_writer', 'solar')",
    )


class UpdateTemplateRequest(BaseModel):
    """Request model for updating a template."""

    content: str = Field(
        ...,
        description="The new content for the template",
    )


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response model."""

    success: bool = Field(..., description="Indicates if the request was successful")
    message: str = Field(..., description="Response message")
    data: T = Field(..., description="Response data")
