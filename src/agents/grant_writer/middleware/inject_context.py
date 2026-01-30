"""
Middleware that builds context (uploaded documents, artifacts, edits) from state
and injects it so the agent prompt and model maintain context.
"""
from langchain.agents.middleware import wrap_model_call
from langchain.agents.middleware.types import ModelRequest, ModelResponse
from typing import Any, Callable


def build_context_from_state(state: dict[str, Any]) -> dict[str, str]:
    """
    Build document_summary, artifacts_summary, artifacts_to_edit_summary, and edits_summary from grant writer state.
    Used by inject_context middleware and by agent_prompt when middleware hasn't run.
    """
    uploaded_documents = state.get("documents", [])
    artifacts = state.get("artifacts", [])
    artifact_edits = state.get("artifact_edits", [])

    # Document summary
    document_summary_parts = []
    for document in uploaded_documents:
        doc_id = document.get("id", "N/A")
        document_type = document.get("document_type", "N/A")
        file_name = document.get("file_name", "N/A")
        purpose = document.get("purpose", "N/A")
        primary_category = document.get("primary_category", "N/A")
        categories = document.get("categories", [])
        how_to_use = document.get("how_to_use", "N/A")
        key_facts = document.get("key_facts", [])
        critical_compliance_rules = document.get("critical_compliance_rules", [])

        doc_info = []
        doc_info.append(f"**ID**: {doc_id}")
        doc_info.append(f"**Document Type**: {document_type}")
        doc_info.append(f"**File Name**: {file_name}")
        doc_info.append(f"**Primary Category**: {primary_category}")
        doc_info.append(f"**Categories**: {', '.join(categories) if categories else 'N/A'}")
        doc_info.append(f"**Purpose**: {purpose}")
        doc_info.append(f"**How to Use**: {how_to_use}")

        if key_facts:
            doc_info.append("**Key Facts**:")
            for fact in key_facts:
                doc_info.append(f"  - {fact}")
        else:
            doc_info.append("**Key Facts**: N/A")

        if critical_compliance_rules:
            doc_info.append("**Critical Compliance Rules**:")
            for rule in critical_compliance_rules:
                doc_info.append(f"  - {rule}")
        else:
            doc_info.append("**Critical Compliance Rules**: N/A")

        document_summary_parts.append("\n".join(doc_info))

    document_summary = (
        "\n\n---\n\n".join(document_summary_parts)
        if document_summary_parts
        else "No documents uploaded."
    )

    # Artifacts summary
    artifacts_summary_parts = []
    for artifact in artifacts:
        artifact_id = artifact.get("id", "N/A")
        document_name = artifact.get("document_name", "N/A")
        timestamp = artifact.get("timestamp", "N/A")
        version = artifact.get("version", "N/A")

        artifact_info = []
        artifact_info.append(f"**ID**: {artifact_id}")
        artifact_info.append(f"**Title**: {document_name}")
        artifact_info.append(f"**Timestamp**: {timestamp}")
        artifact_info.append(f"**Version**: {version}")

        artifacts_summary_parts.append("\n".join(artifact_info))

    artifacts_summary = (
        "\n\n---\n\n".join(artifacts_summary_parts)
        if artifacts_summary_parts
        else "No artifacts generated yet."
    )

    # Artifacts that need editing (identified by read_file; use edit_file for each)
    artifact_id_to_name = {a.get("id"): a.get("document_name", "Unnamed") for a in artifacts if a.get("id")}
    artifacts_to_edit = []
    if isinstance(artifact_edits, list):
        for entry in artifact_edits:
            if not isinstance(entry, dict):
                continue
            aid = entry.get("artifact_id")
            if not isinstance(aid, str) or not aid:
                continue
            # If no edits list exists yet, it means read_file flagged it but edit_file hasn't produced edits.
            if "edits" not in entry:
                artifacts_to_edit.append(aid)
            else:
                edits_list = entry.get("edits", [])
                if isinstance(edits_list, list) and len(edits_list) == 0:
                    artifacts_to_edit.append(aid)
    artifacts_to_edit_parts = []
    for aid in artifacts_to_edit:
        name = artifact_id_to_name.get(aid, "?")
        artifacts_to_edit_parts.append(f"- **ID**: {aid} | **Title**: {name}")
    artifacts_to_edit_summary = (
        "\n".join(artifacts_to_edit_parts)
        if artifacts_to_edit_parts
        else "None (call read_file first to identify artifacts that need editing)."
    )

    # Edits summary (pending edits awaiting user approval), grouped by artifact
    edits_by_artifact: dict[str, list[dict]] = {}
    if isinstance(artifact_edits, list) and artifact_edits:
        for entry in artifact_edits:
            if not isinstance(entry, dict):
                continue
            aid = entry.get("artifact_id", "unknown")
            items = entry.get("edits", [])
            if isinstance(aid, str) and isinstance(items, list):
                edits_by_artifact[aid] = items

    edits_summary_parts = []
    for artifact_id, artifact_edits in edits_by_artifact.items():
        art_name = artifact_id_to_name.get(artifact_id, "Unnamed")
        edits_summary_parts.append(f"**Artifact**: {artifact_id} ({art_name})")
        for edit in artifact_edits:
            edit_id = edit.get("id", "N/A")
            status = edit.get("status", "N/A")
            reasoning = (edit.get("reasoning") or "")[:150]
            text_preview = (edit.get("text_to_replace") or "")[:80].replace("\n", " ")
            replacement_preview = (edit.get("edited_content") or "")[:80].replace("\n", " ")
            edits_summary_parts.append(f"  - Edit {edit_id} [{status}]: \"{text_preview}...\" → \"{replacement_preview}...\" | {reasoning}...")
        edits_summary_parts.append("")

    edits_summary = (
        "\n".join(edits_summary_parts).strip()
        if edits_summary_parts
        else "No pending edits."
    )

    return {
        "document_summary": document_summary,
        "artifacts_summary": artifacts_summary,
        "artifacts_to_edit_summary": artifacts_to_edit_summary,
        "edits_summary": edits_summary,
    }


def _build_context_message(context: dict[str, str]) -> str:
    """Build a single context string for the injected user message."""
    parts = [
        "## Current session context (use when planning and answering; reference these IDs in read_file, edit_file, etc.)",
        "",
        "**Uploaded documents:**",
        context["document_summary"],
        "",
        "**Generated artifacts:**",
        context["artifacts_summary"],
        "",
        "**Artifacts that need editing:** (call edit_file for each; use in parallel when multiple)",
        context["artifacts_to_edit_summary"],
        "",
        "**Pending edits (awaiting user approval):** (grouped by artifact)",
        context["edits_summary"],
    ]
    return "\n".join(parts)


@wrap_model_call
async def inject_context(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    """
    Inject context (uploaded documents, artifacts, edits) from state before recent messages
    so the model maintains session context. Builds a context message and prepends it to
    request.messages; also attaches injected_context for the dynamic prompt.
    """
    state = getattr(request, "state", None) or {}
    context = build_context_from_state(state)
    request.injected_context = context  # type: ignore[attr-defined]

    # Inject context as a user message before recent messages
    context_content = _build_context_message(context)
    messages = getattr(request, "messages", None) or []
    messages = [
        {"role": "user", "content": context_content},
        *messages,
    ]
    if hasattr(request, "override"):
        request = request.override(messages=messages)  # type: ignore[attr-defined]

    return await handler(request)
