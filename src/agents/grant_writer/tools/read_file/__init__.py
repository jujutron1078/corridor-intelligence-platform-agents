"""
Read File Tool

A tool for reading and searching through artifacts and documents to answer user questions.
"""

from .description import TOOL_DESCRIPTION
from .tool import read_file
from .schema import ReadFileInput

__all__ = [
    "TOOL_DESCRIPTION",
    "read_file",
    "ReadFileInput",
]
