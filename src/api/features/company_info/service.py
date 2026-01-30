"""Service layer for company information operations."""

from pathlib import Path
from typing import Optional


def _company_information_dir() -> Path:
    """Return the shared company_information directory path."""
    return Path(__file__).resolve().parent.parent.parent.parent / "shared" / "company_information"


def list_company_info_names() -> list[str]:
    """
    List all company info file names (org names) in the company_information directory.
    Names are derived from filenames without the .md extension.

    Returns:
        Sorted list of org names (e.g. ["bayes"]).
    """
    base = _company_information_dir()
    if not base.exists() or not base.is_dir():
        return []
    names = [f.stem for f in base.glob("*.md")]
    return sorted(names)


def get_company_info_content(org_name: str) -> Optional[str]:
    """
    Load the content of a company info file for the given organization.

    Args:
        org_name: Organization name (file name without .md, e.g. "bayes").

    Returns:
        File content as string, or None if the file does not exist.
    """
    if not (org_name or "").strip():
        return None
    base = _company_information_dir()
    file_path = base / f"{org_name.strip()}.md"
    if not file_path.exists() or not file_path.is_file():
        return None
    try:
        return file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None


def create_company_info(org_name: str, content: str) -> tuple[bool, str]:
    """
    Create a new company info file.

    Args:
        org_name: Organization name (file name without .md).
        content: Markdown content to write.

    Returns:
        Tuple of (success, error_message). error_message is empty on success.
    """
    if not (org_name or "").strip():
        return False, "Organization name is required"
    base = _company_information_dir()
    try:
        base.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return False, f"Failed to create company_information directory: {e}"
    file_path = base / f"{org_name.strip()}.md"
    if file_path.exists():
        return False, f"Company info for '{org_name}' already exists; use update instead"
    try:
        file_path.write_text(content, encoding="utf-8")
        return True, ""
    except Exception as e:
        return False, f"Failed to write file: {e}"


def update_company_info(org_name: str, content: str) -> bool:
    """
    Update the content of an existing company info file.

    Args:
        org_name: Organization name (file name without .md).
        content: New markdown content.

    Returns:
        True if the file was updated successfully, False otherwise.
    """
    if not (org_name or "").strip():
        return False
    base = _company_information_dir()
    file_path = base / f"{org_name.strip()}.md"
    if not file_path.exists():
        return False
    try:
        file_path.write_text(content, encoding="utf-8")
        return True
    except Exception:
        return False


def delete_company_info(org_name: str) -> tuple[bool, str]:
    """
    Delete a company info file.

    Args:
        org_name: Organization name (file name without .md).

    Returns:
        Tuple of (success, error_message). error_message is empty on success.
    """
    if not (org_name or "").strip():
        return False, "Organization name is required"
    base = _company_information_dir()
    file_path = base / f"{org_name.strip()}.md"
    if not file_path.exists():
        return False, f"Company info for '{org_name}' not found"
    try:
        file_path.unlink()
        return True, ""
    except Exception as e:
        return False, f"Failed to delete file: {e}"
