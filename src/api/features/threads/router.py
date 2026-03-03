from fastapi import APIRouter, HTTPException

from src.api.features.threads.schema import CreateThreadRequest, CreateThreadResponse
from src.api.features.threads.service import create_thread, delete_thread
from src.api.schemas import success_response

router = APIRouter(prefix="/threads", tags=["threads"])


@router.post("")
def create_thread_endpoint(request: CreateThreadRequest):
    """Create a thread in a project; stores it in the project's thread.json."""
    try:
        thread_file_path = create_thread(request.thread_id, request.project_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except FileExistsError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except OSError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create thread: {e}",
        ) from e

    data = CreateThreadResponse(
        thread_id=request.thread_id,
        project_id=request.project_id,
        path=str(thread_file_path),
    )
    return success_response("Thread created successfully", data.model_dump())


@router.delete("/{project_id}/{thread_id}")
def delete_thread_endpoint(project_id: str, thread_id: str):
    """Delete a thread from a project."""
    try:
        delete_thread(thread_id, project_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except OSError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete thread: {e}",
        ) from e
    return success_response("Thread deleted successfully", None)
