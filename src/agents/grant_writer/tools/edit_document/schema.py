from pydantic import BaseModel, Field


class EditFileInput(BaseModel):
    """
    The input schema for the edit_file tool.
    """

    artifact_id: str = Field(description="The ID of the artifact (document) to edit.")
    edit_instructions: str = Field(
        description=(
            "Detailed instructions for what changes to make to the document. "
            "Be specific about what sections to modify, what content to add/remove/change, "
            "and any formatting requirements."
        )
    )


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
