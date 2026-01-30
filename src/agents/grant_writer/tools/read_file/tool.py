from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from langchain.chat_models import init_chat_model

from .schema import ReadFileInput, ReadFileOutput
from .description import TOOL_DESCRIPTION
from .prompt import SYSTEM_PROMPT

# Initialize the LLM
llm = init_chat_model(
    model="openai:gpt-5.2",
    streaming=False,
)
structured_llm = llm.with_structured_output(ReadFileOutput)


@tool(description=TOOL_DESCRIPTION)
def read_file(payload: ReadFileInput, runtime: ToolRuntime) -> Command:
    """
    Read a single file (uploaded document or generated artifact) to answer a user's question or determine if editing is needed.

    Finds the file by file_id in uploaded_documents or artifacts, builds the appropriate content block,
    and uses the LLM to answer the question or identify if the artifact needs editing.
    """
    tool_call_id = runtime.tool_call_id
    question = payload.question
    file_id = payload.file_id

    # Get all artifacts from state
    artifacts = runtime.state.get("artifacts", [])
    if not isinstance(artifacts, list):
        artifacts = []

    def _is_int(v) -> bool:
        return isinstance(v, int)

    artifact = None
    if artifacts:
        for art in artifacts:
            if art.get("id") == file_id:
                artifact = art
                break
        # If not found by artifact id, allow reading by stable document_id (latest version).
        if artifact is None:
            candidates = [
                a
                for a in artifacts
                if isinstance(a, dict)
                and (a.get("document_id") == file_id or a.get("id") == file_id)
            ]
            if candidates:
                artifact = max(
                    candidates,
                    key=lambda a: int(a.get("version") or 0) if _is_int(a.get("version")) else 0,
                )

    # If the file_id is an artifact, build the content block for the artifact
    if artifact is not None:
        text_content_block = {
            "type": "text",
            "text": artifact.get("content", ""),
            "document_id": artifact.get("id", ""),
        }
    else:
        text_content_block = None

    # Get the uploaded documents from the state
    uploaded_documents = runtime.state.get("documents", [])

    uploaded_document = None
    if uploaded_documents:
        for doc in uploaded_documents:
            if doc.get("id") == file_id:
                uploaded_document = doc
                break

    # If the file_id is an uploaded document, build the content block for the uploaded document
    if uploaded_document is not None:
        file_data = uploaded_document.get("file_data", "") if isinstance(uploaded_document, dict) else getattr(uploaded_document, "file_data", "")
        file_name = uploaded_document.get("file_name", "") if isinstance(uploaded_document, dict) else getattr(uploaded_document, "file_name", "")
        file_content_block = {
            "type": "file",
            "file": {
                "file_data": file_data,
                "filename": file_name,
            },
        }
    else:
        file_content_block = None

    if text_content_block is None and file_content_block is None:
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        content=f"File with ID '{file_id}' not found.",
                        tool_call_id=tool_call_id,
                    ),
                ],
            },
        )

    user_content = [{"type": "text", "text": question}]
    if text_content_block is not None:
        user_content.append(text_content_block)
    if file_content_block is not None:
        user_content.append(file_content_block)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

    structured_response = structured_llm.invoke(messages)

    # Build response from structured output (ReadFileOutput has how_to_use_file, not response)
    if structured_response.is_file_relevant_to_question:
        response_content = (
            structured_response.how_to_use_file
            or "Relevant to your question."
        )
    else:
        response_content = "Not relevant to your question."

    # If editing is needed and we read an artifact (uploaded files are read-only),
    # record that artifact in `artifact_edits` even before we generate concrete edits.
    artifact_edits_delta = (
        [{"artifact_id": file_id}]
        if (structured_response.needs_editing and artifact is not None)
        else []
    )

    return Command(
        update={
            "messages": [
                ToolMessage(content=response_content, tool_call_id=tool_call_id),
            ],
            "artifact_edits": artifact_edits_delta,
        },
    )
