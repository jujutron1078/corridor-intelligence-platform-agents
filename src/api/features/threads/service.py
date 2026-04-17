import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("corridor.api.threads")

# Project root: src/api/features/threads/service.py -> 5 levels up
WORKSPACES_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "workspaces"

THREADS_FILE = "thread.json"

DEFAULT_THREAD_NAME = "New chat"


def _load_threads(project_path: Path) -> list[dict]:
    path = project_path / THREADS_FILE
    if not path.exists():
        return []
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    threads = data.get("threads")
    if not isinstance(threads, list):
        return []
    return threads


def _save_threads(project_path: Path, threads: list[dict]) -> None:
    path = project_path / THREADS_FILE
    path.write_text(
        json.dumps({"threads": threads}, indent=2),
        encoding="utf-8",
    )


def _validate_project_id(project_id: str) -> Path:
    """Validate project_id against path traversal and return resolved path."""
    if not project_id or ".." in project_id or project_id.startswith(("/", "\\")):
        raise ValueError("Invalid project_id.")
    project_path = (WORKSPACES_DIR / project_id).resolve()
    if not project_path.is_relative_to(WORKSPACES_DIR.resolve()):
        raise ValueError("Invalid project_id.")
    return project_path


def _truncate_name(message: str, max_len: int = 50) -> str:
    """Create a readable thread name by truncating the user's message."""
    text = " ".join(message.split())  # collapse whitespace
    if len(text) <= max_len:
        return text
    truncated = text[:max_len]
    last_space = truncated.rfind(" ")
    if last_space > max_len // 2:
        truncated = truncated[:last_space]
    return truncated + "…"


def create_thread(thread_id: str, project_id: str, name: str = DEFAULT_THREAD_NAME) -> Path:
    """
    Add a thread to the project's thread.json (create file if missing).
    Returns path to thread.json.
    Raises FileNotFoundError if project does not exist.
    Raises FileExistsError if thread_id already exists in that project.
    """
    project_path = _validate_project_id(project_id)
    if not project_path.is_dir():
        raise FileNotFoundError(f"Project '{project_id}' not found.")

    threads = _load_threads(project_path)
    if any(t.get("thread_id") == thread_id for t in threads):
        raise FileExistsError(f"Thread '{thread_id}' already exists in project '{project_id}'.")

    threads.append({
        "thread_id": thread_id,
        "name": name,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    _save_threads(project_path, threads)
    return project_path / THREADS_FILE


def update_thread_name(thread_id: str, project_id: str, name: str) -> str:
    """
    Update the display name of a thread.
    Returns the new name.
    Raises FileNotFoundError if project or thread does not exist.
    """
    project_path = _validate_project_id(project_id)
    if not project_path.is_dir():
        raise FileNotFoundError(f"Project '{project_id}' not found.")

    threads = _load_threads(project_path)
    for t in threads:
        if t.get("thread_id") == thread_id:
            t["name"] = name
            _save_threads(project_path, threads)
            return name

    raise FileNotFoundError(
        f"Thread '{thread_id}' not found in project '{project_id}'."
    )


async def generate_thread_name(message: str) -> str:
    """Generate a short thread name from the user's first message via LLM."""
    from src.api.services.llm_service import llm_call, is_connected

    if not is_connected():
        return _truncate_name(message)

    try:
        result = await llm_call(
            route="simple",
            messages=[{"role": "user", "content": message}],
            system=(
                "Generate a concise 3-6 word title that summarizes this message. "
                "Return ONLY the title text. No quotes, no punctuation at the end."
            ),
        )
        name = result["choices"][0]["message"]["content"].strip().strip("\"'")
        return name[:100] if name else _truncate_name(message)
    except Exception:
        logger.warning("LLM name generation failed, falling back to truncation")
        return _truncate_name(message)


async def generate_and_save_thread_name(
    thread_id: str, project_id: str, message: str
) -> str:
    """
    Generate a name for a thread and save it. Skips if thread already has a
    non-default name.
    """
    project_path = _validate_project_id(project_id)
    if not project_path.is_dir():
        raise FileNotFoundError(f"Project '{project_id}' not found.")

    threads = _load_threads(project_path)
    thread = next((t for t in threads if t.get("thread_id") == thread_id), None)
    if thread is None:
        raise FileNotFoundError(
            f"Thread '{thread_id}' not found in project '{project_id}'."
        )

    # Skip if already named
    existing_name = thread.get("name", "")
    if existing_name and existing_name != DEFAULT_THREAD_NAME:
        return existing_name

    name = await generate_thread_name(message)
    thread["name"] = name
    _save_threads(project_path, threads)
    return name


def delete_thread(thread_id: str, project_id: str) -> None:
    """
    Remove a thread from the project's thread.json.
    Raises FileNotFoundError if project does not exist or thread is not in the project.
    """
    project_path = _validate_project_id(project_id)
    if not project_path.is_dir():
        raise FileNotFoundError(f"Project '{project_id}' not found.")

    threads = _load_threads(project_path)
    new_threads = [t for t in threads if t.get("thread_id") != thread_id]
    if len(new_threads) == len(threads):
        raise FileNotFoundError(
            f"Thread '{thread_id}' not found in project '{project_id}'."
        )
    _save_threads(project_path, new_threads)
