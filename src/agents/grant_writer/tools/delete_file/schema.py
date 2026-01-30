from pydantic import BaseModel, Field


class DeleteFileInput(BaseModel):
    """
    The input schema for the delete_file tool.
    """

    artifact_id: str = Field(
        description="The ID of the artifact (document) to delete. One artifact per call."
    )
