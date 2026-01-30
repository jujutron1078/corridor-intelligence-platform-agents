import uuid
from datetime import datetime

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from langchain.chat_models import init_chat_model

from .schema import EditFileInput, EditFileOutput
from .description import TOOL_DESCRIPTION
from .prompt import EDIT_DOCUMENT_PROMPT

# Initialize the LLM with structured output and reasoning enabled
llm = init_chat_model(
    model="openai:gpt-5.2",
    streaming=False, 
    reasoning_effort="medium",
)
structured_llm = llm.with_structured_output(EditFileOutput)


@tool(description=TOOL_DESCRIPTION)
def edit_file(payload: EditFileInput, runtime: ToolRuntime) -> Command:
    """
    Edit an existing document (artifact) based on user instructions.

    Creates edits that require user approval before applying changes.
    The edits are stored in edits state for UI display and approval.
    """
    tool_call_id = runtime.tool_call_id
    artifact_id = payload.artifact_id
    edit_instructions = payload.edit_instructions

    # Get all artifacts from state
    artifacts = runtime.state.get("artifacts", [])

    # Find the artifact to edit
    artifact = None
    for art in artifacts:
        if art.get("id") == artifact_id:
            artifact = art
            break

    if not artifact:
        available_ids = [a.get("id", "unknown") for a in artifacts]
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        content=f"Artifact with ID '{artifact_id}' not found. Available artifact IDs: {', '.join(available_ids) if available_ids else 'none'}",
                        tool_call_id=tool_call_id,
                    ),
                ],
            }
        )

    # Get original content
    original_content = artifact.get("content", "")
    document_name = artifact.get("document_name", "Unnamed Document")

    if not original_content:
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        content=f"Artifact '{document_name}' has no content to edit.",
                        tool_call_id=tool_call_id,
                    ),
                ],
            }
        )

    # Prepare the edit prompt
    edit_prompt = EDIT_DOCUMENT_PROMPT.format(
        document_name=document_name,
        original_content=original_content,
        edit_instructions=edit_instructions,
    )

    messages = [{"role": "user", "content": edit_prompt}]
    response = structured_llm.invoke(messages)

    edits = response.edits

    # Create edits
    new_edits = []
    for edit in edits:
        new_edits.append(
            {
                "id": str(uuid.uuid4()),
                "artifact_id": artifact_id,
                "reasoning": edit.reasoning,
                "text_to_replace": edit.text_to_replace,
                "edited_content": edit.replacement_content,
                "timestamp": datetime.now().isoformat(),
                "status": "pending",
            }
        )

    return Command(
        update={
            "messages": [
                ToolMessage(content=f"Created {len(new_edits)} edit(s) successfully", tool_call_id=tool_call_id),
            ],
            # Emit only the delta for this artifact; state reducer merges across tool calls.
            "artifact_edits": [{"artifact_id": artifact_id, "edits": new_edits}],
        }
    )
