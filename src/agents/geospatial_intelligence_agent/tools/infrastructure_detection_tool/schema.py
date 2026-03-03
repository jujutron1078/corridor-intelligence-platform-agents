from typing import List, Literal

from pydantic import BaseModel, Field

InfrastructureType = Literal[
    "thermal_power_plant",
    "oil_refinery",
    "port_facility",
    "special_economic_zone",
    "industrial_complex",
    "substation",
    "mining_operation",
]

DETECTION_TYPES_DESCRIPTION = (
    "Infrastructure types to detect. Key types for Abidjan–Lagos: "
    "thermal_power_plant (generation asset, grid interconnection point), "
    "oil_refinery (massive anchor load, e.g. Dangote ≈ 1,000 MW), "
    "port_facility (anchor load + logistics hub), "
    "special_economic_zone (large clustered demand), "
    "industrial_complex (manufacturing anchor load), "
    "substation (existing grid connection point), "
    "mining_operation (remote but high-value anchor load)."
)


class DetectionInput(BaseModel):
    satellite_image_uri: str = Field(description="S3 URI from Tool 3 (fetch_geospatial_layers)")
    types: List[InfrastructureType] = Field(
        description=DETECTION_TYPES_DESCRIPTION,
    )
