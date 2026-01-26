from pydantic import BaseModel, Field
from typing import Optional, Literal


class ReadFileInput(BaseModel):
    """
    The input schema for the read_file tool.
    """

    question: str = Field(
        description="The user's question about the artifacts. This can be a question to answer, or a request to edit a document."
    )


class ReadFileOutput(BaseModel):
    """
    The output schema for the read_file tool.
    """
    action: Literal["provide_response", "edit"] = Field(
        description=(
            "The action to take based on the user's request:\n"
            "- 'provide_response': User asked a question, just provide an answer\n"
            "- 'edit': User wants to edit a document, identify which artifact needs editing"
        )
    )

    response: Optional[str] = Field(
        description="The answer to the user's question or the response about what action will be taken. If action is edit respond with file artifact names that need to be edited."
    )
    
    artifact_id: Optional[list[str]] = Field(
        default=[],
        description="The IDs of the artifacts that need to be edited. Required when action is 'edit'."
    )
    
