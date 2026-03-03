from fastapi import APIRouter, HTTPException

from src.api.features.projects.schema import (
    CreateProjectRequest,
    CreateProjectResponse,
    DeleteProjectResponse,
    ProjectListItem,
)
from src.api.features.projects.service import create_project_folder, delete_project, list_projects
from src.api.schemas import success_response

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("")
def list_projects_endpoint():
    """List all projects in the workspace with project_id, name, and threads."""
    items = list_projects()
    data = [ProjectListItem(**item).model_dump() for item in items]
    return success_response("Projects retrieved successfully", data)


@router.post("")
def create_project(request: CreateProjectRequest):
    """Create a new project folder under workspaces using a slug derived from the project name."""
    try:
        slug, project_path = create_project_folder(request.project_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except FileExistsError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except OSError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create project folder: {e}",
        ) from e

    data = CreateProjectResponse(
        project_name=request.project_name,
        slug=slug,
        path=str(project_path),
    )
    return success_response("Project created successfully", data.model_dump())


@router.delete("/{project_id}")
def delete_project_endpoint(project_id: str):
    """Delete a project and all its data in the workspace."""
    try:
        deleted_id = delete_project(project_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except OSError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete project: {e}",
        ) from e

    data = DeleteProjectResponse(project_id=deleted_id)
    return success_response("Project deleted successfully", data.model_dump())
