import base64
import io
import re
from pathlib import Path
from typing import Any, Optional
from functools import lru_cache
from langchain.tools import ToolRuntime
from pypdf import PdfReader

# Template directory path
TEMPLATES_DIR = Path(__file__).parent.parent.parent.parent.parent / "shared" / "templates" / "grant_writer"


def _scan_templates_directory() -> dict[str, str]:
    """
    Internal function to scan the templates directory.
    Called once at module load time to avoid blocking calls during runtime.
    
    Returns:
        Dict mapping document_type to template filename (e.g., {"cover_letter": "cover_letter.md"})
    """
    document_types: dict[str, str] = {}
    
    if not TEMPLATES_DIR.exists():
        return document_types
    
    # Use list() to eagerly evaluate the generator at load time
    for template_file in list(TEMPLATES_DIR.glob("*.md")):
        # Convert filename to document type: cover_letter.md -> cover_letter
        document_type = template_file.stem
        document_types[document_type] = template_file.name
    
    return document_types


# Cache the document types at module load time to avoid blocking calls during requests
_CACHED_DOCUMENT_TYPES: dict[str, str] = _scan_templates_directory()

# Also cache the template contents to avoid repeated file reads
_CACHED_TEMPLATES: dict[str, str] = {}


def refresh_document_types_cache() -> None:
    """
    Refresh the cached document types by rescanning the templates directory.
    Call this if templates are added/removed at runtime.
    """
    global _CACHED_DOCUMENT_TYPES, _CACHED_TEMPLATES
    _CACHED_DOCUMENT_TYPES = _scan_templates_directory()
    _CACHED_TEMPLATES.clear()


def get_document_types() -> dict[str, str]:
    """
    Get the cached document types mapping.
    
    Returns:
        Dict mapping document_type to template filename.
    """
    return _CACHED_DOCUMENT_TYPES


def get_available_document_types() -> list[str]:
    """
    Get a list of all available document types (from cache).
    
    Returns:
        Sorted list of document type names.
    """
    return sorted(_CACHED_DOCUMENT_TYPES.keys())


def is_valid_document_type(document_type: str) -> bool:
    """
    Check if a document type is valid (has a corresponding template).
    
    Args:
        document_type: The document type to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    return document_type in _CACHED_DOCUMENT_TYPES


def load_template(document_type: str) -> Optional[str]:
    """
    Load a template file based on the document type.
    Uses caching to avoid repeated file reads.
    
    Args:
        document_type: The type of document (e.g., 'technical_proposal', 'cover_letter')
        
    Returns:
        The template content as a string, or None if no template exists for this type.
    """
    # Check cache first
    if document_type in _CACHED_TEMPLATES:
        return _CACHED_TEMPLATES[document_type]
    
    template_filename = _CACHED_DOCUMENT_TYPES.get(document_type)
    
    if not template_filename:
        return None
    
    template_path = TEMPLATES_DIR / template_filename
    
    if not template_path.exists():
        return None
    
    # Read and cache the template content
    content = template_path.read_text(encoding="utf-8")
    _CACHED_TEMPLATES[document_type] = content
    
    return content


@lru_cache(maxsize=1)
def get_document_types_for_prompt() -> str:
    """
    Generate a formatted string of available document types for use in prompts.
    Cached since the result rarely changes.
    
    Returns:
        Formatted string listing all available document types.
    """
    document_types = get_available_document_types()
    
    if not document_types:
        return "No document templates available."
    
    # Format each document type with a description derived from the name
    lines = []
    for doc_type in document_types:
        # Convert snake_case to readable format: technical_proposal -> Technical Proposal
        readable_name = doc_type.replace("_", " ").title()
        lines.append(f"- `{doc_type}` - {readable_name}")
    
    return "\n".join(lines)


def get_documents_index(runtime: ToolRuntime) -> dict[str, dict[str, Any]]:
    """
    Index GrantWriterState.documents (list[Document]) by Document.id.
    Normalizes each Document into a plain dict via model_dump().
    """
    docs = runtime.state.get("documents", [])
    index: dict[str, dict[str, Any]] = {}

    for d in docs:
        if hasattr(d, "model_dump"):
            doc = d.model_dump()
        elif isinstance(d, dict):
            doc = d
        else:
            continue

        doc_id = doc.get("id")
        if isinstance(doc_id, str) and doc_id:
            index[doc_id] = doc

    return index


def resolve_doc(index: dict[str, dict[str, Any]], doc_id: str) -> Optional[dict[str, Any]]:
    return index.get(doc_id) if doc_id else None


def doc_brief(doc: dict[str, Any]) -> dict[str, Any]:
    """A compact representation to feed into the LLM prompt."""
    return {
        "id": doc.get("id"),
        "file_name": doc.get("file_name"),
        "primary_category": doc.get("primary_category"),
        "categories": doc.get("categories", []),
        "purpose": doc.get("purpose"),
        "how_to_use": doc.get("how_to_use"),
        "key_facts": doc.get("key_facts", []),
        "critical_compliance_rules": doc.get("critical_compliance_rules", []),
    }


# Company info directory path
COMPANY_INFO_DIR = Path(__file__).parent.parent.parent / "company_info"

# Cache for all company info loaded at module time
_CACHED_COMPANY_CONTEXT: Optional[str] = None


def _load_all_company_info() -> str:
    """
    Load all company info files from the company_info directory at module load time.
    Combines all .md files into a single string.
    
    Returns:
        Combined company info content from all files.
    """
    if not COMPANY_INFO_DIR.exists():
        return "No company information available."
    
    all_content: list[str] = []
    
    for info_file in sorted(COMPANY_INFO_DIR.glob("*.md")):
        content = info_file.read_text(encoding="utf-8")
        all_content.append(content)
    
    if not all_content:
        return "No company information available."
    
    return "\n\n---\n\n".join(all_content)


# Load all company context at module load time
_CACHED_COMPANY_CONTEXT = _load_all_company_info()


def get_company_context() -> str:
    """
    Get the cached company context (all company info files combined).
    
    Returns:
        Combined company context string.
    """
    return _CACHED_COMPANY_CONTEXT or "No company information available."


def extract_base64_content(file_data: str) -> tuple[bytes, str]:
    """
    Extract binary content and mime type from a data URL or raw base64 string.
    
    Args:
        file_data: Data URL (e.g., 'data:application/pdf;base64,...') or raw base64 string
        
    Returns:
        Tuple of (decoded_bytes, mime_type)
    """
    # Check if it's a data URL
    data_url_pattern = r'^data:([^;]+);base64,(.+)$'
    match = re.match(data_url_pattern, file_data, re.DOTALL)
    
    if match:
        mime_type = match.group(1)
        base64_content = match.group(2)
    else:
        # Assume raw base64 and try to detect type
        mime_type = "application/octet-stream"
        base64_content = file_data
    
    # Decode base64 to bytes
    decoded_bytes = base64.b64decode(base64_content)
    
    return decoded_bytes, mime_type


def pdf_bytes_to_text(pdf_bytes: bytes) -> str:
    """
    Extract text from PDF bytes using pypdf.
    
    Args:
        pdf_bytes: Raw PDF file bytes
        
    Returns:
        Extracted text from all pages
    """
    pdf_file = io.BytesIO(pdf_bytes)
    reader = PdfReader(pdf_file)
    
    text_parts: list[str] = []
    for page_num, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text()
        if page_text:
            text_parts.append(f"--- Page {page_num} ---\n{page_text}")
    
    return "\n\n".join(text_parts) if text_parts else ""


def convert_file_data_to_text(file_data: str, filename: str = "") -> str:
    """
    Convert base64-encoded file data to plain text.
    Supports PDF files; other formats return raw decoded content or a notice.
    
    Args:
        file_data: Base64-encoded file data (data URL or raw base64)
        filename: Optional filename to help determine file type
        
    Returns:
        Extracted text content from the file
    """
    if not file_data:
        return ""
    
    try:
        decoded_bytes, mime_type = extract_base64_content(file_data)
        
        # Determine file type from mime type or filename
        is_pdf = (
            mime_type == "application/pdf" or 
            filename.lower().endswith(".pdf")
        )
        
        if is_pdf:
            return pdf_bytes_to_text(decoded_bytes)
        
        # For text-based files, try to decode as UTF-8
        is_text = mime_type.startswith("text/") or filename.lower().endswith((".txt", ".md", ".csv"))
        if is_text:
            return decoded_bytes.decode("utf-8", errors="replace")
        
        # For other file types, return a notice
        return f"[Binary file: {filename or 'unknown'} ({mime_type}) - content extraction not supported]"
        
    except Exception as e:
        return f"[Error extracting content from {filename or 'file'}: {str(e)}]"


def get_document_content_as_text(doc: dict[str, Any]) -> str:
    """
    Get the text content of a document, converting from base64 if needed.
    
    Args:
        doc: Document dict with file_data and file_name fields
        
    Returns:
        Text content of the document
    """
    file_data = doc.get("file_data", "")
    filename = doc.get("file_name", "")
    
    return convert_file_data_to_text(file_data, filename)
