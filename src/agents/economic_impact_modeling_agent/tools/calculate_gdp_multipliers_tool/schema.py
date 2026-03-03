from pydantic import BaseModel, Field


class GDPMultiplierInput(BaseModel):
    total_capex: float = Field(
        ..., description="Total transmission investment from the Financial Agent."
    )
    industrial_output: float = Field(
        ..., description="Estimated annual production value from anchor loads."
    )
    region_io_model: str = Field(
        default="West_Africa_2024_IO",
        description="The Input-Output model for the corridor.",
    )
