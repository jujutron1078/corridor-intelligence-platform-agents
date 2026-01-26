from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from langchain.chat_models import init_chat_model

from .schema import ReadFileInput, ReadFileOutput
from .description import TOOL_DESCRIPTION
from .prompt import SYSTEM_PROMPT, USER_PROMPT

# Initialize the LLM
llm = init_chat_model(
    model="openai:gpt-5.2",
    streaming=False,
    reasoning_effort="medium",
)
structured_llm = llm.with_structured_output(ReadFileOutput)


@tool(description=TOOL_DESCRIPTION)
def read_file(payload: ReadFileInput, runtime: ToolRuntime) -> Command:
    """
    Read all artifacts to answer a user's question or determine if editing is needed.

    Reads all artifacts (generated documents) from the state and uses their content
    to either answer the user's question or determine if the user wants to edit a document.
    """
    tool_call_id = runtime.tool_call_id
    question = payload.question

    # Get all artifacts from state
    artifacts = runtime.state.get("artifacts", [])

    print(f"Artifacts: {artifacts}")

    if not artifacts:
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        content="No document has been generated yet. Please generate a document first.",
                        tool_call_id=tool_call_id,
                    ),
                ],
            }
        )

    # Build artifact content for LLM
    full_artifact_content = []
    for idx, artifact in enumerate(artifacts, start=1):
        artifact_id = artifact.get("id", "unknown")
        artifact_name = artifact.get("document_name", "Unnamed Document")
        artifact_content = artifact.get("content", "")
        artifact_timestamp = artifact.get("timestamp", "")
        artifact_version = artifact.get("version", 1)

        full_artifact_content.append(
            f"Artifact {idx}:\n"
            f"  ID: {artifact_id}\n"
            f"  Name: {artifact_name}\n"
            f"  Version: {artifact_version}\n"
            f"  Timestamp: {artifact_timestamp}\n"
            f"  Content: {artifact_content}\n"
        )

    full_content = "\n".join(full_artifact_content)

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT.format(
                artifact_content=full_content, question=question
            ),
        },
        {
            "role": "user",
            "content": USER_PROMPT,
        },
    ]

    structured_response = structured_llm.invoke(messages)

    # Ensure artifact_id is always a list (not None)
    artifact_ids = (
        structured_response.artifact_id
        if structured_response.artifact_id is not None
        else []
    )

    # Ensure response is not None
    response_content = (
        structured_response.response if structured_response.response is not None else ""
    )

    return Command(
        update={
            "messages": [
                ToolMessage(content=response_content, tool_call_id=tool_call_id),
            ],
            "artifacts_to_edit": artifact_ids,
        }
    )
