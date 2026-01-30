from langchain.agents import AgentState
from typing import TypedDict, Annotated, Literal, NotRequired
import operator

from src.shared.schema.document_schema import Document


class Artifact(TypedDict):
    """Generated document artifact with metadata."""
    id: str
    # Stable identifier for the logical document across versions.
    # For v1, this is set to the artifact's own id. Subsequent versions share the same document_id.
    document_id: NotRequired[str]
    # The artifact id this version was regenerated from (if any).
    parent_id: NotRequired[str]
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

class ArtifactEdits(TypedDict):
    """Edits for an artifact."""
    artifact_id: str
    edits: NotRequired[list[PendingEdit]]

def _merge_pending_edits(left: list[PendingEdit] | None, right: list[PendingEdit]) -> list[PendingEdit]:
    """Append/merge edits; de-dupe by edit id (last write wins)."""
    merged = (left or []) + right
    by_id: dict[str, PendingEdit] = {}
    order: list[str] = []
    extras: list[PendingEdit] = []
    for edit in merged:
        edit_id = None
        if isinstance(edit, dict):
            edit_id = edit.get("id")
        if isinstance(edit_id, str) and edit_id:
            if edit_id not in by_id:
                order.append(edit_id)
            by_id[edit_id] = edit
        else:
            extras.append(edit)
    return [by_id[i] for i in order] + extras


def merge_artifact_edits(left: list[ArtifactEdits] | None, right) -> list[ArtifactEdits]:
    """
    Reducer for `artifact_edits` (list of {"artifact_id": "...", "edits"?: [...]}).

    - If `right` is a list: treat as delta updates and merge by artifact_id.
    - If `right` is {"op": "replace", "items": [...] }: replace entire list.

    Notes:
    - If a delta item omits `edits`, we keep existing edits as-is (if any).
    - If a delta item includes `edits`, we APPEND/MERGE into that artifact's existing edits list.
    """
    if right is None:
        return left or []

    if isinstance(right, dict) and right.get("op") == "replace":
        items = right.get("items", [])
        return items if isinstance(items, list) else (left or [])

    if not isinstance(right, list):
        return left or []

    merged: dict[str, ArtifactEdits] = {}
    order: list[str] = []

    def upsert(entry: dict) -> None:
        aid = entry.get("artifact_id")
        if not isinstance(aid, str) or not aid:
            return
        if aid not in order:
            order.append(aid)

        existing = merged.get(aid, {"artifact_id": aid})
        if "edits" in entry:
            edits_val = entry.get("edits")
            if isinstance(edits_val, list):
                existing["edits"] = _merge_pending_edits(existing.get("edits", []), edits_val)
            else:
                # If explicitly provided but not a list, normalize to empty list
                existing["edits"] = []
        merged[aid] = existing

    for e in (left or []):
        if isinstance(e, dict):
            upsert(e)

    for e in right:
        if isinstance(e, dict):
            upsert(e)

    return [merged[aid] for aid in order]


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


class GrantWriterState(AgentState):
    """State for the grant writer agent."""
    documents: Annotated[list[Document], operator.add]
    artifacts: Annotated[list[Artifact], replace_artifacts_list]
    artifact_edits: Annotated[list[ArtifactEdits], merge_artifact_edits]