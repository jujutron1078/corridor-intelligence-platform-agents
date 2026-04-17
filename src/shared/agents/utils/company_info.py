"""
Load company information from shared markdown files.

org_name is the file name without .md (e.g. "bayes" loads company_information/bayes.md).
"""

from pathlib import Path


def load_company_info_text(org_name: str) -> str:
    """
    Load company information text for the given organization.

    org_name: File name without extension (e.g. "bayes" → company_information/bayes.md).

    Returns:
        File contents as string, or empty string if file not found.
    """
    if not (org_name or "").strip():
        return ""

    # Resolve path: src/shared/company_information/{org_name}.md
    base = Path(__file__).resolve().parent.parent  # src/shared
    file_path = base / "company_information" / f"{org_name.strip()}.md"

    if not file_path.exists() or not file_path.is_file():
        return ""

    return file_path.read_text(encoding="utf-8", errors="ignore")
