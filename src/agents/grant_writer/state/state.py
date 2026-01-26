from langchain.agents import AgentState
from typing import TypedDict, Annotated, Literal
import operator

from src.shared.schema.document_schema import Document


class Artifact(TypedDict):
    """Generated document artifact with metadata."""
    id: str
    document_name: str
    content: str
    timestamp: str
    version: int
    approved: bool = False


class PendingEdit(TypedDict):
    """Pending document edit awaiting user approval."""
    id: str
    artifact_id: str
    reasoning: str  # The model's reasoning process for this edit
    text_to_replace: str  # Exact text in the document to be replaced
    edited_content: str  # Replacement content for the text_to_replace
    timestamp: str
    status: Literal["pending", "accepted", "rejected"]


def replace_artifacts_list(left: list[Artifact], right: list[Artifact]) -> list[Artifact]:
    """
    Custom reducer for artifacts list.
    
    - If right is provided and is a list, it replaces left (for deletion/replacement)
    - This allows tools to replace the entire artifacts list when needed
    """
    if right is None:
        return left or []
    # Always replace with the new list (right takes precedence)
    return right if isinstance(right, list) else (left or [])


def replace_edits_list(left: list[PendingEdit], right: list[PendingEdit]) -> list[PendingEdit]:
    """
    Custom reducer for edits list.
    
    - If right is provided and is a list, it replaces left (for updates)
    - This allows tools to replace the entire edits list when needed
    """
    if right is None:
        return left or []
    # Always replace with the new list (right takes precedence)
    return right if isinstance(right, list) else (left or [])


class GrantWriterState(AgentState):
    """State for the grant writer agent."""
    documents: Annotated[list[Document], operator.add]
    artifacts: Annotated[list[Artifact], replace_artifacts_list]
    artifacts_to_edit: Annotated[list[str], operator.add]
    edits: Annotated[list[PendingEdit], replace_edits_list]