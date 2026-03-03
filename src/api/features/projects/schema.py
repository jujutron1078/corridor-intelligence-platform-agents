from pydantic import BaseModel, Field


class CreateProjectRequest(BaseModel):
    project_name: str = Field(..., min_length=1, description="Display name of the project")


class CreateProjectResponse(BaseModel):
    project_name: str
    slug: str
    path: str


class ProjectListItem(BaseModel):
    project_id: str
    name: str
    threads: list[dict]


class DeleteProjectResponse(BaseModel):
    project_id: str
