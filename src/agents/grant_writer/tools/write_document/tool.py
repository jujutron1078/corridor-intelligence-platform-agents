from datetime import datetime

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from langchain.chat_models import init_chat_model

from src.shared.utils.doc_ids import make_artifact_id
from .schema import WriteDocumentInput
from .description import TOOL_DESCRIPTION
from .prompt import AGENT_PROMPT
from .progress import ProgressTracker
from .messages import PROGRESS_SUB_MESSAGES
from .utils import get_documents_index, resolve_doc, load_template, get_company_context, get_document_content_as_text

# Initialize the LLM with reasoning enabled
llm = init_chat_model(
    model="openai:gpt-5.2",
    streaming=False,
    reasoning_effort="medium",
)


@tool(description=TOOL_DESCRIPTION)
def write_document(payload: WriteDocumentInput, runtime: ToolRuntime) -> Command:
    """
    Write a complete, final document based on gathered structured context.

    Supports two modes:
      - open_generation: use references (and optional constraints) to generate a donor-facing doc
      - fill_template: follow the canonical structure in template_document_id, using references
    """

    tool_call_id = runtime.tool_call_id

    # Use artifact-{type}-{short_id} format (e.g. artifact-technical-proposal-a1b2c3d4)
    if payload.generation_mode == "open_generation":
        doc_id = make_artifact_id(payload.document_type or "document")
    elif payload.generation_mode == "fill_template":
        doc_id = make_artifact_id(payload.document_name or "document")
    else:
        doc_id = make_artifact_id("document")
    progress = ProgressTracker(runtime.stream_writer, doc_id, payload.document_name)

    # Get the document id and check if it exists in the state
    progress.update("Starting document generation process...")
    progress.update("Checking if the document identifier you provided is valid...")

    # WE FIRST HANDLE WHEN THE MODE IS open_generation
    if payload.generation_mode == "open_generation":
        progress.update("Using open generation mode...")
        # Get the document type
        progress.update("Validating document type...")
        document_type = payload.document_type

        if not document_type:
            return Command(
                update={
                    "messages": [
                        ToolMessage(
                            content="document_type is required when generation_mode='open_generation'."
                        )
                    ],
                }
            )

        # Load the template based on document type
        progress.update(f"Loading template for document type: {document_type}...")
        template_content = load_template(document_type)


        if template_content:
            progress.update(f"Loaded template for {document_type}...")
        else:
            progress.update(
                f"No predefined template for {document_type}, generating with default structure..."
            )

        # Get the reference documents to use during generation
        progress.update("Retrieving reference documents...")
        docs_index = get_documents_index(runtime)
        reference_docs = [
            resolve_doc(docs_index, ref_id)
            for ref_id in payload.reference_document_ids
            if resolve_doc(docs_index, ref_id)
        ]

        progress.update(f"Processing {len(reference_docs)} reference document(s)...")

        # Build content blocks for LLM message (file attachments)
        reference_document_content_blocks: list[dict] = []
        
        # Build metadata string for each reference document
        reference_documents_metadata: list[str] = []

        for idx, ref_doc in enumerate(reference_docs, start=1):
            file_name = ref_doc.get("file_name", "Unknown")
            progress.update(f"Processing reference document {idx}/{len(reference_docs)}: {file_name}...")
            file_name = ref_doc.get("file_name", "Unknown")
            file_data = ref_doc.get("file_data")
            
            # Add file content block if file_data exists
            if file_data:
                reference_document_content_blocks.append(
                    {
                        "type": "file",
                        "file": {
                            "file_data": file_data,
                            "filename": file_name,
                        },
                    }
                )
            
            # Build metadata for this document
            doc_metadata_lines = [
                f"### Reference Document {idx}: {file_name}",
                f"**ID**: {ref_doc.get('id', 'N/A')}",
                f"**Primary Category**: {ref_doc.get('primary_category', 'N/A')}",
                f"**Categories**: {', '.join(ref_doc.get('categories', [])) or 'N/A'}",
                f"**Purpose**: {ref_doc.get('purpose', 'N/A')}",
                f"**How to Use**: {ref_doc.get('how_to_use', 'N/A')}",
            ]
            
            # Add key facts if present
            key_facts = ref_doc.get("key_facts", [])
            if key_facts:
                doc_metadata_lines.append("**Key Facts**:")
                for fact in key_facts:
                    doc_metadata_lines.append(f"  - {fact}")
            
            # Add critical compliance rules if present
            compliance_rules = ref_doc.get("critical_compliance_rules", [])
            if compliance_rules:
                doc_metadata_lines.append("**Critical Compliance Rules**:")
                for rule in compliance_rules:
                    doc_metadata_lines.append(f"  - {rule}")
            
            reference_documents_metadata.append("\n".join(doc_metadata_lines))

        # Join all document metadata with separators
        progress.update("Compiling reference document metadata...")
        reference_documents_prompt_string = (
            "\n\n---\n\n".join(reference_documents_metadata) 
            if reference_documents_metadata 
            else "No reference documents provided."
        )

        # get the document name
        document_name = payload.document_name

        # get the context
        context = payload.context

        # get the reasoning
        reasoning = payload.reasoning

        # get the constraints
        constraints = payload.constraints

        # get the must_include
        must_include = payload.must_include

        # get the must_not_include
        must_not_include = payload.must_not_include

        # get the audience
        audience = payload.audience

        # get the tone
        tone = payload.tone

        # Get company context (loaded at module init from all company_info files)
        progress.update("Loading company context...")
        company_context = get_company_context()

        # Build system message
        progress.update("Building system prompt with all context and instructions...")
        system_instruction = AGENT_PROMPT.format(
            document_name=document_name,
            company_context=company_context,
            evidence_documents=reference_documents_prompt_string,
            context=context,
            reasoning=reasoning,
            constraints=constraints,
            must_include=must_include,
            must_not_include=must_not_include,
            audience=audience,
            tone=tone,
            template_content=template_content,
        )

        progress.update("Preparing messages for LLM...")
        messages = [
            {
                "role": "system",
                "content": system_instruction,
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Document name: {document_name}, make sure the following template is followed: {template_content}"},
                    *reference_document_content_blocks,
                ],
            },
        ]
        progress.update("Writing the document...", sub_messages=PROGRESS_SUB_MESSAGES)
        response = llm.invoke(messages)
        progress.update("Processing LLM response...")
        generated_document = response.content
        progress.update("Document generation completed successfully!")
        
        # Get existing artifacts and append the new one
        existing_artifacts = runtime.state.get("artifacts", [])
        new_artifact = {
            "id": doc_id,
            "document_name": document_name,
            "content": generated_document,
            "timestamp": datetime.now().isoformat(),
            "version": 1,
            "approved": False,
        }
        updated_artifacts = existing_artifacts + [new_artifact]
        
        return Command(
            update={
                "artifacts": updated_artifacts,
                "messages": [
                    ToolMessage(content=f"Document {document_name} generated successfully.", tool_call_id=tool_call_id),
                ],
            }
        )

    # Handle fill_template mode
    if payload.generation_mode == "fill_template":
        progress.update("Using fill template mode...")

        # Check if the template document id is provided
        if not payload.template_document_id:
            return Command(
                update={
                    "messages": [
                        ToolMessage(content="template_document_id is required to fill the template.", tool_call_id=tool_call_id),
                    ],
                }
            )

        # Get the template document and convert from base64 to text
        progress.update(f"Retrieving template document (ID: {payload.template_document_id})...")
        docs_index = get_documents_index(runtime)
        template_document = resolve_doc(docs_index, payload.template_document_id)
        
        if not template_document:
            return Command(
                update={
                    "messages": [
                        ToolMessage(content=f"Template document with id '{payload.template_document_id}' not found.", tool_call_id=tool_call_id),
                    ],
                }
            )
        
        # Convert template from base64 (PDF/other) to text
        template_filename = template_document.get("file_name", "template")
        progress.update(f"Extracting content from template document: {template_filename}...")
        template_content = get_document_content_as_text(template_document)
        
        if not template_content or template_content.startswith("[Error"):
            return Command(
                update={
                    "messages": [
                        ToolMessage(content=f"Failed to extract content from template document '{template_filename}'.", tool_call_id=tool_call_id),
                    ],
                }
            )
        
        progress.update(f"Loaded template from {template_filename}...")

        # Get the reference documents to use during generation
        progress.update("Retrieving reference documents for template filling...")
        reference_docs = [
            resolve_doc(docs_index, ref_id)
            for ref_id in payload.reference_document_ids
            if resolve_doc(docs_index, ref_id)
        ]

        progress.update(f"Processing {len(reference_docs)} reference document(s) for template filling...")

        # Build content blocks for LLM message (file attachments)
        reference_document_content_blocks: list[dict] = []
        
        # Build metadata string for each reference document
        reference_documents_metadata: list[str] = []

        for idx, ref_doc in enumerate(reference_docs, start=1):
            file_name = ref_doc.get("file_name", "Unknown")
            progress.update(f"Processing reference document {idx}/{len(reference_docs)}: {file_name}...")
            file_name = ref_doc.get("file_name", "Unknown")
            file_data = ref_doc.get("file_data")
            
            # Add file content block if file_data exists
            if file_data:
                reference_document_content_blocks.append(
                    {
                        "type": "file",
                        "file": {
                            "file_data": file_data,
                            "filename": file_name,
                        },
                    }
                )
            
            # Build metadata for this document
            doc_metadata_lines = [
                f"### Reference Document {idx}: {file_name}",
                f"**ID**: {ref_doc.get('id', 'N/A')}",
                f"**Primary Category**: {ref_doc.get('primary_category', 'N/A')}",
                f"**Categories**: {', '.join(ref_doc.get('categories', [])) or 'N/A'}",
                f"**Purpose**: {ref_doc.get('purpose', 'N/A')}",
                f"**How to Use**: {ref_doc.get('how_to_use', 'N/A')}",
            ]
            
            # Add key facts if present
            key_facts = ref_doc.get("key_facts", [])
            if key_facts:
                doc_metadata_lines.append("**Key Facts**:")
                for fact in key_facts:
                    doc_metadata_lines.append(f"  - {fact}")
            
            # Add critical compliance rules if present
            compliance_rules = ref_doc.get("critical_compliance_rules", [])
            if compliance_rules:
                doc_metadata_lines.append("**Critical Compliance Rules**:")
                for rule in compliance_rules:
                    doc_metadata_lines.append(f"  - {rule}")
            
            reference_documents_metadata.append("\n".join(doc_metadata_lines))

        # Join all document metadata with separators
        progress.update("Compiling reference document metadata for template filling...")
        reference_documents_prompt_string = (
            "\n\n---\n\n".join(reference_documents_metadata) 
            if reference_documents_metadata 
            else "No reference documents provided."
        )

        # Extract parameters from payload
        document_name = payload.document_name
        context = payload.context
        reasoning = payload.reasoning
        constraints = payload.constraints
        must_include = payload.must_include
        must_not_include = payload.must_not_include
        audience = payload.audience
        tone = payload.tone

        # Get company context
        progress.update("Loading company context for template filling...")
        company_context = get_company_context()

        # Build system message
        progress.update("Building system prompt with template and context...")
        system_instruction = AGENT_PROMPT.format(
            document_name=document_name,
            company_context=company_context,
            evidence_documents=reference_documents_prompt_string,
            context=context,
            reasoning=reasoning,
            constraints=constraints,
            must_include=must_include,
            must_not_include=must_not_include,
            audience=audience,
            tone=tone,
            template_content=template_content,
        )

        progress.update("Preparing messages for LLM template filling...")
        messages = [
            {
                "role": "system",
                "content": system_instruction,
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Fill the following template exactly: {template_filename}"},
                    *reference_document_content_blocks,
                ],
            },
        ]
        
        progress.update("Writing the document...", sub_messages=PROGRESS_SUB_MESSAGES)
        response = llm.invoke(messages)
        progress.update("Processing LLM response...")
        generated_document = response.content
        progress.update("Template filling completed successfully!")
        
        # Get existing artifacts and append the new one
        existing_artifacts = runtime.state.get("artifacts", [])
        new_artifact = {
            "id": doc_id,
            "document_name": document_name,
            "content": generated_document,
            "timestamp": datetime.now().isoformat(),
            "version": 1,
            "approved": False,
        }
        updated_artifacts = existing_artifacts + [new_artifact]
        
        return Command(
            update={
                "artifacts": updated_artifacts,
                "messages": [
                    ToolMessage(content=f"Document {document_name} generated successfully.", tool_call_id=tool_call_id),
                ],
            }
        )

    raise ValueError(f"Unsupported generation mode: {payload.generation_mode}")

