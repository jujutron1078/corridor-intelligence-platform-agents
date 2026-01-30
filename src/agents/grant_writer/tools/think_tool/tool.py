from typing import Optional

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage, HumanMessage
from langgraph.types import Command

from src.shared.schema.document_schema import Document
from src.shared.utils.doc_ids import make_doc_id
from .description import THINK_TOOL_DESCRIPTION
from .utils import extract_uploaded_files_from_message, replace_file_blocks_with_document_summary



@tool(description=THINK_TOOL_DESCRIPTION)
def think_tool(
    reflection: str,
    runtime: ToolRuntime,
    documents: Optional[list[Document]] = None,
) -> Command:
    """
    Reflect on the results of each delegated task and plan next steps.
    """

    # Get existing messages
    messages = runtime.state.get("messages", [])
    new_messages = list(messages)

    # Extract uploaded files from the most recent human message (typically right before tool call)
    last_message = messages[-2] if len(messages) >= 2 else (messages[-1] if messages else None)
    uploaded_files: list[dict] = extract_uploaded_files_from_message(last_message) if last_message else []

    if uploaded_files:
        print(f"Extracted {len(uploaded_files)} uploaded files: {[f.get('filename') for f in uploaded_files]}")

    # Once we have the uploaded files extracted from the message, create/normalize a list of Document objects
    # and add the uploaded file details (e.g., filename + file_data) onto each Document.
    normalized_documents: list[Document] = list(documents) if documents else []

    # If the model didn't provide document metadata but files exist, create placeholder Document objects
    # so downstream tools/state always get a consistent `documents` list.
    if uploaded_files and not normalized_documents:
        normalized_documents = [
            Document(
                id="",
                file_name="",
                file_data="",
                purpose="",
                primary_category="OTHER",
                categories=["OTHER"],
                how_to_use="",
                key_facts=[],
                critical_compliance_rules=[],
            )
            for _ in uploaded_files
        ]

    # Attach real uploaded file metadata (match by index)
    for i, doc in enumerate(normalized_documents):
        if i < len(uploaded_files):
            uploaded = uploaded_files[i]
            # Use doc-{type}-{short_id} format; prefer document_type, else primary_category (e.g. doc-rfp-a1b2c3d4)
            type_for_id = getattr(doc, "document_type", None) or getattr(doc, "primary_category", None) or "OTHER"
            doc.id = doc.id or make_doc_id(type_for_id)
            # Always trust the system-extracted filename as the final filename
            doc.file_name = (uploaded.get("filename") or "") or doc.file_name
            doc.file_data = doc.file_data or (uploaded.get("file_data") or "")

            # Defensive defaults if the model omitted fields or provided partial metadata
            if not getattr(doc, "primary_category", None):
                doc.primary_category = "OTHER"
            if not getattr(doc, "categories", None):
                doc.categories = [doc.primary_category]
            if doc.primary_category not in doc.categories:
                doc.categories = [doc.primary_category, *doc.categories]

    # Filter out documents with empty file_data - they are not useful
    valid_documents = [doc for doc in normalized_documents if doc.file_data]
    
    if len(valid_documents) < len(normalized_documents):
        discarded_count = len(normalized_documents) - len(valid_documents)
        print(f"Discarded {discarded_count} document(s) with empty file_data")

    # Replace file blocks in the last message with document summaries to save context space
    if uploaded_files and last_message and isinstance(last_message, HumanMessage) and valid_documents:
        last_message.content = replace_file_blocks_with_document_summary(last_message.content, valid_documents)
        print("Replaced file blocks with document summaries in message")

    # Add the tool message
    tool_message = ToolMessage(
        content=reflection,
        tool_call_id=runtime.tool_call_id,
    )
    new_messages.append(tool_message)
    
    # Build the state update
    state_update = {
        "messages": new_messages,
    }
    
    # Convert Pydantic models to dicts for state storage - only include valid documents with file_data
    if valid_documents:
        state_update["documents"] = [doc.model_dump() for doc in valid_documents]

    return Command(update=state_update)
