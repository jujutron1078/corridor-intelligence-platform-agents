import re
import shutil
from pathlib import Path

import yaml

# Project root: src/api/features/projects/service.py -> 5 levels up
WORKSPACES_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "workspaces"

PROJECT_MD = "PROJECT.md"


def name_to_slug(name: str) -> str:
    """Convert project name to a URL/filesystem-safe slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[-\s]+", "-", slug)
    return slug.strip("-") or "project"


def create_project_folder(project_name: str) -> tuple[str, Path]:
    """
    Create project directory under workspaces and PROJECT.md with frontmatter.
    Returns (slug, project_path).
    Raises ValueError for invalid slug, FileExistsError if project exists, OSError on mkdir failure.
    """
    slug = name_to_slug(project_name)
    if not slug:
        raise ValueError("Project name could not be converted to a valid slug.")

    project_path = WORKSPACES_DIR / slug
    if project_path.exists():
        raise FileExistsError(f"Project with slug '{slug}' already exists.")

    project_path.mkdir(parents=True, exist_ok=False)

    safe_name = project_name.replace("\\", "\\\\").replace('"', '\\"')
    (project_path / PROJECT_MD).write_text(
        f"---\nproject_name: \"{safe_name}\"\n---\n\n",
        encoding="utf-8",
    )

    return slug, project_path


def _project_name_from_md(project_path: Path) -> str:
    """Read project name from PROJECT.md frontmatter. Fallback to folder name if missing/invalid."""
    path = project_path / PROJECT_MD
    if not path.exists():
        return project_path.name
    raw = path.read_text(encoding="utf-8")
    if not raw.strip().startswith("---"):
        return project_path.name
    parts = raw.split("---", 2)
    if len(parts) < 2:
        return project_path.name
    try:
        front = yaml.safe_load(parts[1])
        if isinstance(front, dict) and "project_name" in front:
            return str(front["project_name"]).strip() or project_path.name
    except Exception:
        pass
    return project_path.name


def list_projects() -> list[dict]:
    """
    List all projects under workspaces. Each item has project_id, name, and threads.
    Uses threads from thread.json when present.
    """
    from src.api.features.threads.service import _load_threads

    if not WORKSPACES_DIR.exists():
        return []

    result = []
    for path in sorted(WORKSPACES_DIR.iterdir()):
        if not path.is_dir():
            continue
        project_id = path.name
        name = _project_name_from_md(path)
        threads = _load_threads(path)
        result.append({
            "project_id": project_id,
            "name": name,
            "threads": threads,
        })
    return result


def delete_project(project_id: str) -> str:
    """
    Delete a project folder and all its contents under workspaces.
    Returns the deleted project_id.
    Raises FileNotFoundError if project does not exist.
    Raises ValueError if project_id is invalid (e.g. path traversal).
    """
    if not project_id or ".." in project_id or project_id.startswith("/"):
        raise ValueError("Invalid project_id.")
    project_path = WORKSPACES_DIR / project_id
    if not project_path.exists():
        raise FileNotFoundError(f"Project '{project_id}' not found.")
    if not project_path.is_dir():
        raise FileNotFoundError(f"Project '{project_id}' is not a directory.")
    # Ensure we don't escape workspaces (resolve and check it's a subpath)
    resolved = project_path.resolve()
    workspaces_resolved = WORKSPACES_DIR.resolve()
    try:
        resolved.relative_to(workspaces_resolved)
    except ValueError:
        raise ValueError("Invalid project_id.") from None
    shutil.rmtree(project_path)
    return project_id
