import json
import logging

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import DetectionInput

logger = logging.getLogger("corridor.agent.geospatial.infrastructure_detection")


@tool("infrastructure_detection", description=TOOL_DESCRIPTION)
def infrastructure_detection_tool(
    payload: DetectionInput, runtime: ToolRuntime
) -> Command:
    """
    Detects infrastructure points within the corridor using OSM + USGS data.

    Returns physical infrastructure locations (ports, airports, power plants,
    industrial zones, rail, mineral sites, border crossings) with coordinates
    and metadata from real pipeline services.
    """
    from src.adapters.pipeline_bridge import pipeline_bridge

    try:
        infra = pipeline_bridge.get_infrastructure_detections()

        # Add energy data for power-related detections
        try:
            energy = pipeline_bridge.get_energy_data()
            plants = energy.get("power_plants", {}).get("features", [])
            for i, feat in enumerate(plants):
                coords = feat.get("geometry", {}).get("coordinates", [])
                props = feat.get("properties", {})
                infra["detections"].append({
                    "detection_id": f"DET-PWR-{i+1:03d}",
                    "type": "power_plant",
                    "name": props.get("name", "Unknown Power Plant"),
                    "coordinates": coords,
                    "confidence": 0.95,
                    "source": "Global Power Plant Database",
                    "properties": {
                        "fuel": props.get("fuel_type", "unknown"),
                        "capacity_mw": props.get("capacity_mw", 0),
                        "country": props.get("country", ""),
                        "is_anchor_load": True,
                        "is_generation_asset": True,
                    },
                })
            infra["detection_count"] = len(infra["detections"])
        except Exception as exc:
            logger.warning("Energy data enrichment failed: %s", exc)

        response = {
            "job_metadata": {
                "corridor_id": "AL_CORRIDOR_001",
                "data_sources": ["OpenStreetMap", "USGS Minerals", "Global Power Plant DB"],
            },
            "detection_count": infra.get("detection_count", 0),
            "detections": infra.get("detections", []),
            "status": infra.get("status", "Infrastructure Detections Complete"),
        }

        # Enrich with existing transmission grid infrastructure
        try:
            grid_data = pipeline_bridge.get_transmission_grid()
            grid_info = grid_data.get("grid", {})
            response["grid_infrastructure"] = {
                "transmission_lines": grid_info.get("transmission_lines", []),
                "substations": grid_info.get("substations", []),
                "summary": grid_data.get("summary", {}),
                "source": grid_data.get("source", "Transmission Grid Database"),
            }
            response["job_metadata"]["data_sources"].append("Transmission Grid DB")
            logger.info("Transmission grid data added: %d lines, %d substations",
                         len(grid_info.get("transmission_lines", [])),
                         len(grid_info.get("substations", [])))
        except Exception as exc:
            logger.warning("Transmission grid data unavailable: %s", exc)

        # Enrich with planned energy generation sites
        try:
            planned = pipeline_bridge.get_planned_energy_projects()
            projects = planned.get("projects", [])
            response["planned_generation"] = {
                "projects": projects,
                "capacity_summary": planned.get("capacity_summary", {}),
                "source": planned.get("source", "Energy Projects Database"),
            }
            response["job_metadata"]["data_sources"].append("Planned Energy Projects")
            logger.info("Planned energy projects added: %d", len(projects))
        except Exception as exc:
            logger.warning("Planned energy projects unavailable: %s", exc)

    except Exception as exc:
        logger.error("Infrastructure detection failed: %s", exc)
        response = {
            "error": str(exc),
            "detection_count": 0,
            "detections": [],
            "message": "Infrastructure detection failed. Check OSM/mineral service initialization.",
        }

    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=json.dumps(response), tool_call_id=runtime.tool_call_id
                )
            ]
        }
    )
