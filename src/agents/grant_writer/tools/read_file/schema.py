from pydantic import BaseModel, Field
from typing import Optional, Literal


class ReadFileInput(BaseModel):
    """
    The input schema for the read_file tool.
    """

    question: str = Field(
        description="The user's question about the artifacts. This can be a question to answer, or a request to edit a document."
    )
    file_id: str = Field(
        description="The ID of the file to read. This is the ID of the file that the user wants to read."
    )


class ReadFileOutput(BaseModel):
    """
    The output schema for the read_file tool.
    """

    is_file_relevant_to_question: bool = Field(
        description="True if file helps answer question or needs editing. False otherwise."
    )

    needs_editing: bool = Field(
        description="True if this artifact needs editing per user's request. False for uploaded docs (read-only) or informational queries."
    )

    how_to_use_file: Optional[str] = Field(
        description="""How to use this file. None if not relevant.

For info extraction: What to extract | How to interpret | How to use | Context
For editing: What to edit | Why | How | Impact

Example (info): "EXTRACT: Deadline 'March 15, 2025' from Section 2.3 | Hard deadline, timezone EAT | Use as submission target | Late = auto-reject"

Example (edit): "EDIT: Timeline '4 months' → '6 months' | User extending duration | Update Summary, Work Plan, Gantt | Also update Financial Proposal"

Be concise and actionable.
"""
    )
