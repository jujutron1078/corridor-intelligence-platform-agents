from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .schema import DeleteFileInput
from .description import TOOL_DESCRIPTION 


@tool(description=TOOL_DESCRIPTION)
def delete_file(payload: DeleteFileInput, runtime: ToolRuntime) -> Command:
    """
    Delete one or more artifacts (generated documents) from the state.
    
    Removes the specified artifacts from the artifacts list in the state.
    """
    tool_call_id = runtime.tool_call_id
    artifact_ids = payload.artifact_ids
    
    # Validate input
    if not artifact_ids:
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        content="No artifact IDs provided. Please provide at least one artifact ID to delete.",
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
    artifact_ids_set = set(artifact_ids)
    deleted_artifacts = []
    remaining_artifacts = []
    
    # Separate deleted from remaining
    for artifact in artifacts:
        if artifact.get("id") in artifact_ids_set:
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
    
    # Get current edits and filter out edits associated with deleted artifacts
    edits = runtime.state.get("edits", [])
    remaining_edits = [
        edit for edit in edits 
        if edit.get("artifact_id") not in artifact_ids_set
    ]
    deleted_edits_count = len(edits) - len(remaining_edits)
    
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
            "edits": remaining_edits,  # Update state with filtered edits
        }
    )