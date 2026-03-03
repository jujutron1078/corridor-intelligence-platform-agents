from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class StandardSuccessResponse(BaseModel, Generic[T]):
    """Standard success envelope: { success: true, message: str, data: T }."""

    success: bool = True
    message: str
    data: T


class StandardErrorResponse(BaseModel):
    """Standard error envelope: { success: false, message: str, data: null }."""

    success: bool = False
    message: str
    data: None = None


def success_response(message: str, data: Any) -> dict[str, Any]:
    """Build a standard success payload for JSON response."""
    return {"success": True, "message": message, "data": data}


def error_response(message: str) -> dict[str, Any]:
    """Build a standard error payload for JSON response."""
    return {"success": False, "message": message, "data": None}
