from pydantic import BaseModel, Field


class CreateThreadRequest(BaseModel):
    thread_id: str = Field(..., min_length=1, description="Unique identifier for the thread")
    project_id: str = Field(..., min_length=1, description="Project slug (folder name under workspaces)")


class CreateThreadResponse(BaseModel):
    thread_id: str
    project_id: str
    path: str
