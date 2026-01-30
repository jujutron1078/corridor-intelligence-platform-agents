"""
ID generation for grant writer documents and artifacts.

Format:
- Uploaded documents: doc-{type}-{short_id}  (e.g. doc-rfp-123, doc-compliance-a1b2c3d4)
- Generated artifacts: artifact-{type}-{short_id}  (e.g. artifact-proposal-456, artifact-cover-letter-e5f6g7h8)
"""
import re
import uuid


def _slug(text: str) -> str:
    """Normalize to a short slug: lowercase, single hyphens, alphanumeric + hyphen only."""
    if not text or not isinstance(text, str):
        return "doc"
    s = text.strip().lower()
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"[^a-z0-9-]", "", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "doc"


def make_doc_id(category: str) -> str:
    """
    Generate an ID for an uploaded document.

    Args:
        category: Document category or type (e.g. COMPLIANCE, REFERENCE, or derived from filename like "rfp").

    Returns:
        ID in format doc-{type}-{short_id}, e.g. doc-compliance-a1b2c3d4.
    """
    slug = _slug(category) if category else "doc"
    short_id = uuid.uuid4().hex[:8]
    return f"doc-{slug}-{short_id}"


def make_artifact_id(type_or_name: str) -> str:
    """
    Generate an ID for a generated artifact.

    Args:
        type_or_name: Document type (e.g. technical_proposal) or document name (e.g. "Technical Proposal").

    Returns:
        ID in format artifact-{type}-{short_id}, e.g. artifact-technical-proposal-a1b2c3d4.
    """
    slug = _slug(type_or_name) if type_or_name else "artifact"
    short_id = uuid.uuid4().hex[:8]
    return f"artifact-{slug}-{short_id}"
