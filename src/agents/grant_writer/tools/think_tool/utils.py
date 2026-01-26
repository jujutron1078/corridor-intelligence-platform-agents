from langchain_core.messages import HumanMessage

from src.shared.schema.document_schema import Document


def extract_uploaded_files_from_message(message) -> list[dict]:
    """
    Extract uploaded files from a single message.
    
    Scans through message content looking for file attachments in the format:
    - type: file
      file:
        file_data: data:application/pdf;base64,...
        filename: example.pdf
    
    Returns a list of dicts with type, text, mime_type, and filename.
    The text field will be populated later with the document description.
    """
    uploaded_files = []
    
    if not isinstance(message, HumanMessage):
        return uploaded_files
    
    content = message.content
    
    # Content can be a string or a list of content blocks
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "file":
                file_info = block.get("file", {})
                file_data = file_info.get("file_data")
                filename = file_info.get("filename")
                
                if file_data and filename:
                
                    uploaded_files.append({
                        "file_data": file_data,
                        "filename": filename
                    })
    
    return uploaded_files




def replace_file_blocks_with_document_summary(content, documents: list[Document]) -> list:
    """
    Replace file blocks in message content with text blocks containing document metadata.
    
    This reduces context space by replacing large base64 file data with concise
    markdown summaries containing the document description and key facts.
    
    Args:
        content: Original message content (string or list of content blocks)
        documents: List of Document objects with extracted metadata
        
    Returns:
        Modified content with file blocks replaced by text blocks
    """
    # If content is a string, return as is (no files to replace)
    if isinstance(content, str):
        return content
    
    # If content is not a list, return as is
    if not isinstance(content, list):
        return content
    
    modified_content = []
    file_index = 0
    
    for block in content:
        # If it's a file block and we have a corresponding document
        if isinstance(block, dict) and block.get("type") == "file":
            if file_index < len(documents):
                doc = documents[file_index]
                
                # Build a compact summary of the document (text-only block)
                primary = getattr(doc, "primary_category", None) or "OTHER"
                categories = getattr(doc, "categories", None) or []
                summary_parts = [
                    f"[📎 {doc.file_name or 'Uploaded File'} | {primary}]\n",
                    f"ID: {doc.id}\n",
                ]
                if categories:
                    summary_parts.append(f"Categories: {', '.join(categories)}\n")
                if doc.purpose:
                    summary_parts.append(f"Purpose: {doc.purpose}\n")
                
                if doc.key_facts:
                    summary_parts.append("Key facts:\n")
                    for fact in doc.key_facts:
                        summary_parts.append(f"- {fact}\n")
                
                if doc.critical_compliance_rules:
                    summary_parts.append("Critical compliance rules:\n")
                    for rule in doc.critical_compliance_rules:
                        summary_parts.append(f"- {rule}\n")
                
                if doc.how_to_use:
                    summary_parts.append(f"How to use: {doc.how_to_use}\n")
                
                # Replace file block with text block (using standard TextContentBlock format)
                modified_content.append({
                    "type": "text",
                    "text": "".join(summary_parts),
                    "document_id": doc.id,
                })
                
                file_index += 1
            else:
                # No corresponding document, keep original file block
                modified_content.append(block)
        else:
            # Keep non-file blocks as is
            modified_content.append(block)
    
    return modified_content
