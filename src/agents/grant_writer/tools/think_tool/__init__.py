"""
Think Tool

A tool for reflecting on task results and planning next steps.
"""

from src.shared.schema.document_schema import Document, Category
from .description import THINK_TOOL_DESCRIPTION
from .utils import extract_uploaded_files_from_message, replace_file_blocks_with_document_summary
from .tool import think_tool

__all__ = [
    "Document",
    "Category",
    "THINK_TOOL_DESCRIPTION",
    "extract_uploaded_files_from_message",
    "replace_file_blocks_with_document_summary",
    "think_tool",
]
