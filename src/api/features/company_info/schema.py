"""Schema definitions for company info endpoints."""

from pydantic import BaseModel, Field
from typing import Generic, TypeVar

T = TypeVar("T")


class UpdateCompanyInfoRequest(BaseModel):
    """Request model for creating or updating company info."""

    content: str = Field(
        ...,
        description="The markdown content for the company information file",
    )


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response model."""

    success: bool = Field(..., description="Indicates if the request was successful")
    message: str = Field(..., description="Response message")
    data: T = Field(..., description="Response data")
