from pydantic import BaseModel, Field


class DeleteFileInput(BaseModel):
    """
    The input schema for the delete_file tool.
    """

    artifact_ids: list[str] = Field(
        description="The IDs of the artifacts (documents) to delete. Can be a single ID or multiple IDs."
    )
