import json
from datetime import datetime, timezone
from pathlib import Path

# Project root: src/api/features/threads/service.py -> 5 levels up
WORKSPACES_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "workspaces"

THREADS_FILE = "thread.json"


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


def create_thread(thread_id: str, project_id: str) -> Path:
    """
    Add a thread to the project's thread.json (create file if missing).
    Returns path to thread.json.
    Raises FileNotFoundError if project does not exist.
    Raises FileExistsError if thread_id already exists in that project.
    """
    project_path = WORKSPACES_DIR / project_id
    if not project_path.is_dir():
        raise FileNotFoundError(f"Project '{project_id}' not found.")

    threads = _load_threads(project_path)
    if any(t.get("thread_id") == thread_id for t in threads):
        raise FileExistsError(f"Thread '{thread_id}' already exists in project '{project_id}'.")

    threads.append({
        "thread_id": thread_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    _save_threads(project_path, threads)
    return project_path / THREADS_FILE


def delete_thread(thread_id: str, project_id: str) -> None:
    """
    Remove a thread from the project's thread.json.
    Raises FileNotFoundError if project does not exist or thread is not in the project.
    """
    project_path = WORKSPACES_DIR / project_id
    if not project_path.is_dir():
        raise FileNotFoundError(f"Project '{project_id}' not found.")

    threads = _load_threads(project_path)
    new_threads = [t for t in threads if t.get("thread_id") != thread_id]
    if len(new_threads) == len(threads):
        raise FileNotFoundError(
            f"Thread '{thread_id}' not found in project '{project_id}'."
        )
    _save_threads(project_path, new_threads)
