from fastapi import APIRouter, HTTPException

from src.api.features.threads.schema import (
    CreateThreadRequest,
    CreateThreadResponse,
    GenerateThreadNameRequest,
    UpdateThreadNameRequest,
)
from src.api.features.threads.service import (
    create_thread,
    delete_thread,
    generate_and_save_thread_name,
    update_thread_name,
)
from src.api.schemas import success_response

router = APIRouter(prefix="/threads", tags=["threads"])


@router.post("")
def create_thread_endpoint(request: CreateThreadRequest):
    """Create a thread in a project; stores it in the project's thread.json."""
    try:
        thread_file_path = create_thread(request.thread_id, request.project_id, request.name)
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
        name=request.name,
    )
    return success_response("Thread created successfully", data.model_dump())


@router.patch("/{project_id}/{thread_id}")
def update_thread_name_endpoint(
    project_id: str, thread_id: str, request: UpdateThreadNameRequest
):
    """Update the display name of a thread."""
    try:
        name = update_thread_name(thread_id, project_id, request.name)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except OSError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    return success_response(
        "Thread renamed",
        {"thread_id": thread_id, "project_id": project_id, "name": name},
    )


@router.post("/{project_id}/{thread_id}/generate-name")
async def generate_name_endpoint(
    project_id: str, thread_id: str, request: GenerateThreadNameRequest
):
    """Generate a short display name from the user's first message and save it."""
    try:
        name = await generate_and_save_thread_name(thread_id, project_id, request.message)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except OSError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    return success_response(
        "Thread name generated",
        {"thread_id": thread_id, "project_id": project_id, "name": name},
    )


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
