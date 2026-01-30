from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional

from .utils import get_available_document_types, is_valid_document_type


GenerationMode = Literal["fill_template", "open_generation"]


class WriteDocumentInput(BaseModel):
    """
    The input schema for the write_document tool.
    
    Document types are dynamically discovered from the templates folder.
    """

    document_name: str = Field(
        description="The name we are going to give this document'"
    )

    generation_mode: GenerationMode = Field(
        default="open_generation",
        description="Use 'fill_template' when a strict template must be followed.",
    )

    document_type: Optional[str] = Field(
        default=None,
        description=(
            "Required when generation_mode='open_generation'. "
            "The type of document to generate. "
        ),
    )

    @field_validator("document_type")
    @classmethod
    def validate_document_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate that document_type exists in the templates folder."""
        if v is None:
            return v
        
        if not is_valid_document_type(v):
            available = get_available_document_types()
            raise ValueError(
                f"Invalid document_type '{v}'. "
                f"Available types: {', '.join(available) if available else 'none (no templates found)'}"
            )
        return v

    template_document_id: Optional[str] = Field(
        default=None,
        description="If provided, this document is the canonical structure to fill. Required when generation_mode='fill_template'.",
    )

    reference_document_ids: list[str] = Field(
        default_factory=list,
        description="Documents to consult as evidence/rules/scope/policies (ToR, ITT instructions, policies, etc.).",
    )

    context: str = Field(
        description="Relevant user-provided context and requirements gathered from chat."
    )
    reasoning: str = Field(
        description="Why this doc is being generated; how the references should be used."
    )

    constraints: list[str] = Field(
        default_factory=list,
        description="Hard constraints: page limits, font rules, deadlines, required sections, etc.",
    )
    must_include: list[str] = Field(
        default_factory=list,
        description="Explicit sections/items that must appear in the final document.",
    )
    must_not_include: list[str] = Field(
        default_factory=list,
        description="Things to avoid (e.g., excluded pricing details in technical proposal).",
    )
    audience: Optional[str] = Field(
        default=None,
        description="Who this is written for (donor evaluators, client, internal).",
    )
    tone: Optional[str] = Field(
        default=None,
        description="Voice/tone guidance (formal, donor-facing, concise, etc.).",
    )
