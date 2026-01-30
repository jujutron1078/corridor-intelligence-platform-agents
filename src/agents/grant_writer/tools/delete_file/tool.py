from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .schema import DeleteFileInput
from .description import TOOL_DESCRIPTION 


@tool(description=TOOL_DESCRIPTION)
def delete_file(payload: DeleteFileInput, runtime: ToolRuntime) -> Command:
    """
    Delete a single artifact (generated document) from the state.
    
    Removes the specified artifact from the artifacts list in the state.
    """
    tool_call_id = runtime.tool_call_id
    artifact_id = payload.artifact_id
    
    # Validate input
    if not artifact_id:
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        content="No artifact ID provided. Please provide an artifact ID to delete.",
                        tool_call_id=tool_call_id,
                    ),
                ],
            }
        )
    
    # Get current artifacts
    artifacts = runtime.state.get("artifacts", [])
    if not artifacts:
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        content="No artifacts found in the state.",
                        tool_call_id=tool_call_id,
                    ),
                ],
            }
        )
    
    # Track results
    deleted_artifacts = []
    remaining_artifacts = []
    
    # Separate deleted from remaining
    for artifact in artifacts:
        if artifact.get("id") == artifact_id:
            deleted_artifacts.append(artifact.get("document_name", "Unknown"))
        else:
            remaining_artifacts.append(artifact)
    
    # Build response
    if not deleted_artifacts:
        available_ids = [a.get("id", "unknown") for a in artifacts]
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        content=f"No matching artifacts found. Available IDs: {', '.join(available_ids)}",
                        tool_call_id=tool_call_id,
                    ),
                ],
            }
        )
    
    # Get current edits (grouped by artifact) and drop deleted artifacts' edits
    artifact_edits = runtime.state.get("artifact_edits", []) or []
    if not isinstance(artifact_edits, list):
        artifact_edits = []

    deleted_edits_count = 0
    remaining_artifact_edits = []
    for entry in artifact_edits:
        if not isinstance(entry, dict):
            continue
        aid = entry.get("artifact_id")
        if aid == artifact_id:
            edits = entry.get("edits", [])
            if isinstance(edits, list):
                deleted_edits_count += len(edits)
            continue
        remaining_artifact_edits.append(entry)
    
    # Success case
    deleted_count = len(deleted_artifacts)
    message_parts = [
        f"Deleted {deleted_count} artifact{'s' if deleted_count > 1 else ''}:\n"
        + "\n".join(f"  • {name}" for name in deleted_artifacts)
    ]
    
    if deleted_edits_count > 0:
        message_parts.append(
            f"\nAlso deleted {deleted_edits_count} associated edit{'s' if deleted_edits_count > 1 else ''}."
        )
    
    message = "".join(message_parts)
    
    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=message,
                    tool_call_id=tool_call_id,
                ),
            ],
            "artifacts": remaining_artifacts,  # Update state with filtered list
            "artifact_edits": {"op": "replace", "items": remaining_artifact_edits},
        }
    )