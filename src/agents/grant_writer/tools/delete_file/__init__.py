"""
Delete File Tool

A tool for deleting artifacts (generated documents) from the state.
"""

from .description import TOOL_DESCRIPTION
from .tool import delete_file
from .schema import DeleteFileInput

__all__ = [
    "TOOL_DESCRIPTION",
    "delete_file",
    "DeleteFileInput",
]
