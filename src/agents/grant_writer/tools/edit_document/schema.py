from pydantic import BaseModel, Field, model_validator
from typing import Optional


class EditFileInput(BaseModel):
    """
    The input schema for the edit_file tool.
    """

    artifact_id: Optional[str] = Field(
        default=None,
        description=(
            "Optional. The ID of the specific artifact (document version) to edit. "
            "If provided, takes precedence over document_id/from_version."
        ),
    )

    document_id: Optional[str] = Field(
        default=None,
        description=(
            "Optional. Stable logical document identifier shared across versions. "
            "If provided (and artifact_id is omitted), the latest version will be edited by default."
        ),
    )

    from_version: Optional[int] = Field(
        default=None,
        description=(
            "Optional. When editing by document_id, choose which version to edit. "
            "If omitted, the latest version is used."
        ),
    )

    edit_instructions: str = Field(
        description=(
            "Detailed instructions for what changes to make to the document. "
            "Be specific about what sections to modify, what content to add/remove/change, "
            "and any formatting requirements."
        )
    )

    @model_validator(mode="after")
    def validate_target(self) -> "EditFileInput":
        if not self.artifact_id and not self.document_id:
            raise ValueError("Provide either artifact_id or document_id")
        if self.from_version is not None and self.from_version < 1:
            raise ValueError("from_version must be >= 1")
        return self


class PendingEdit(BaseModel):
    """
    The schema for a pending edit to be applied to the document.
    """
    reasoning: str = Field(
        description=(
            "Your reasoning process for this edit. Explain: "
            "1) What text you identified that needs to be changed, "
            "2) How you located the exact text to replace in the document, "
            "3) Why this specific text match is correct, "
            "4) What the replacement content should be and why. "
            "This reasoning must come BEFORE determining the text_to_replace and replacement_content values."
        )
    )
    text_to_replace: str = Field(
        description=(
            "The exact text in the original document that needs to be replaced. "
            "This must be the EXACT text as it appears in the document, including all whitespace, punctuation, and formatting. "
            "The system will use string find-and-replace to locate and replace this exact text. "
            "If the text appears multiple times and you want to replace all occurrences, create separate edits for each occurrence, "
            "or if you want to replace only a specific occurrence, include enough surrounding context to make it unique."
        )
    )
    replacement_content: str = Field(
        description=(
            "The replacement content that should replace the text_to_replace in the original document. "
            "This should be the new text that will replace the exact text_to_replace when the edit is applied. "
            "Maintain formatting, structure, and style consistent with the surrounding content."
        )
    )


class EditFileOutput(BaseModel):
    """
    The structured output schema for the edit_file tool's LLM response.
    """

    edits: list[PendingEdit] = Field(
        description="The list of pending edits to be applied to the document."
    )
