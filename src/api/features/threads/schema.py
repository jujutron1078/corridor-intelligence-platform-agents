from pydantic import BaseModel, Field


class CreateThreadRequest(BaseModel):
    thread_id: str = Field(..., min_length=1, description="Unique identifier for the thread")
    project_id: str = Field(..., min_length=1, description="Project slug (folder name under workspaces)")
    name: str = Field(default="New chat", max_length=100, description="Display name for the thread")


class CreateThreadResponse(BaseModel):
    thread_id: str
    project_id: str
    path: str
    name: str


class UpdateThreadNameRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="New display name")


class GenerateThreadNameRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User message to generate a title from")
