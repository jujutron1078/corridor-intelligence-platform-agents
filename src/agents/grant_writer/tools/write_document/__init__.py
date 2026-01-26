"""
Write Document Tool

A tool for generating complete, final documents based on structured context.
"""

from .schema import WriteDocumentInput
from .description import TOOL_DESCRIPTION
from .prompt import AGENT_PROMPT
from .messages import PROGRESS_SUB_MESSAGES
from .progress import ProgressTracker
from .tool import write_document

__all__ = [
    "WriteDocumentInput",
    "TOOL_DESCRIPTION",
    "AGENT_PROMPT",
    "PROGRESS_SUB_MESSAGES",
    "ProgressTracker",
    "write_document",
]
