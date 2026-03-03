import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import DetectionInput


@tool("infrastructure_detection", description=TOOL_DESCRIPTION)
def infrastructure_detection_tool(
    payload: DetectionInput, runtime: ToolRuntime
) -> Command:
    """
    Runs computer vision inference on satellite imagery to detect
    infrastructure points physically visible within the corridor boundary.

    This tool ONLY returns what satellite imagery can physically observe:
    - Facility type and physical subtype
    - Coordinates and bounding box
    - Confidence score and verification status
    - Visible physical attributes (cooling towers, berths, tanks, cranes, etc.)
    - Change detection (new construction activity since last census)
    - Whether the detection matched a known asset registry (yes/no only)
    - Routing flags: is_anchor_load, is_generation_asset (yes/no only)
    - Road safety flags: is_road_safety_risk, risk_severity (yes/no + severity level)

    This tool does NOT return:
    - Company or operator names       → handled by scan_anchor_loads
    - Power demand estimates (MW)     → handled by calculate_current_demand
    - Off-take quality / credit       → handled by assess_bankability
    - Load profiles                   → handled by calculate_current_demand
    - Demand at buildout              → handled by model_growth_trajectory

    Road Safety Detection Types:
    - Roadside Market — High Pedestrian Density
    - Uncontrolled High-Speed Junction
    - School or Hospital — Road Proximity Zone
    - Informal Settlement — Road Edge Encroachment
    - Sharp Curve — Limited Sight Distance
    - Border Crossing — Congestion & Pedestrian Mix Zone
    - Livestock & Agricultural Crossing Zone
    - Fuel Station — Unsignalised Entry/Exit
    - Truck Layby — Informal Roadside Parking
    - Road Works — Active Construction Zone

    Risk Severity Scale:
    - CRITICAL: Immediate danger, fatal accident risk
    - HIGH:     Significant hazard requiring design mitigation
    - MEDIUM:   Moderate risk requiring monitoring and signage
    - LOW:      Minor risk, standard design measures sufficient

    Corridor boundary applied:
        Top-Left    (NW): [-4.008, 5.600]
        Top-Right   (NE): [ 3.379, 6.750]
        Bottom-Right(SE): [ 3.379, 6.250]
        Bottom-Left (SW): [-4.008, 5.100]
    Only detections whose coordinates fall within this polygon are returned.
    """

    response = {
        "job_metadata": {
            "tool": "infrastructure_detection",
            "corridor_id": "ABIDJAN_LAGOS_CORRIDOR",
            "corridor_boundary": {
                "type": "Polygon",
                "coordinates": [[
                    [-4.008, 5.600],   # Top-Left     (NW — Abidjan north)
                    [ 3.379, 6.750],   # Top-Right    (NE — Lagos north)
                    [ 3.379, 6.250],   # Bottom-Right (SE — Lagos south)
                    [-4.008, 5.100],   # Bottom-Left  (SW — Abidjan south)
                    [-4.008, 5.600],   # Close polygon
                ]],
                "note": (
                    "All detections are filtered to this bounding polygon. "
                    "Facilities outside this boundary are excluded regardless "
                    "of detection confidence."
                ),
            },
            "source_raster": (
                "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                "satellite/sentinel2_median_2025H2_10m.tif"
            ),
            "model": {
                "name": "CorridorNet-v2",
                "backbone": "YOLOv8x (fine-tuned)",
                "training_dataset": (
                    "AfricaInfra-500K (547,000 labelled African infrastructure tiles) "
                    "+ RoadSafe-West-Africa-120K (120,000 labelled road safety tiles)"
                ),
                "input_tile_size_px": 640,
                "tile_overlap_pct": 20,
                "total_tiles_processed": 18742,
                "inference_device": "GPU (NVIDIA A10G)",
                "processing_time_seconds": 498,
            },
            "detection_thresholds": {
                "min_confidence_to_include": 0.45,
                "auto_verified_above": 0.85,
                "manual_review_required_below": 0.70,
            },
            "generated_at": "2026-01-26T09:18:44+00:00",
        },

        # ------------------------------------------------------------------ #
        #  DETECTIONS                                                         #
        #  Fields per detection:                                              #
        #    detection_id, type, subtype, coordinates, bounding_box,         #
        #    confidence, verification_status, facility_attributes,            #
        #    change_detection, matched_known_asset (bool only),               #
        #    is_anchor_load (bool), is_generation_asset (bool),               #
        #    is_road_safety_risk (bool), risk_severity (str | None)           #
        #                                                                     #
        #  Fields intentionally ABSENT (belong to downstream agents):        #
        #    label / operator name   → scan_anchor_loads                      #
        #    estimated_power_demand_mw → calculate_current_demand             #
        #    off_take_quality        → assess_bankability                     #
        #    load_profile            → calculate_current_demand               #
        #    demand_at_full_buildout → model_growth_trajectory                #
        # ------------------------------------------------------------------ #
        "detections": [

            # ================================================================
            # SECTION A: ENERGY & ECONOMIC INFRASTRUCTURE DETECTIONS
            # (Original DET-001 through DET-035 — unchanged)
            # ================================================================

            # ── CÔTE D'IVOIRE ─────────────────────────────────────────────

            {
                "detection_id": "DET-001",
                "type": "thermal_power_plant",
                "subtype": "Combined Cycle Gas Turbine (CCGT)",
                "matched_known_asset": True,
                "coordinates": {"latitude": 5.302, "longitude": -4.025},
                "bounding_box": {
                    "top_left":     {"latitude": 5.308, "longitude": -4.032},
                    "bottom_right": {"latitude": 5.296, "longitude": -4.018},
                },
                "confidence": 0.97,
                "verification_status": "auto_verified",
                "facility_attributes": {
                    "estimated_footprint_sqm": 142000,
                    "visible_cooling_towers": 2,
                    "visible_stack_count": 1,
                    "transmission_lines_egressing": 3,
                    "on_site_substation_detected": True,
                },
                "change_detection": {
                    "is_new_since_last_census": False,
                    "last_census_date": "2023-01-01",
                    "construction_activity_detected": True,
                    "change_note": (
                        "New transformer bay visible — consistent with a planned "
                        "expansion phase; additional conductor strings being strung."
                    ),
                },
                "is_anchor_load": False,
                "is_generation_asset": True,
                "is_road_safety_risk": False,
                "risk_severity": None,
            },

            {
                "detection_id": "DET-002",
                "type": "thermal_power_plant",
                "subtype": "Combined Cycle Gas Turbine (CCGT)",
                "matched_known_asset": True,
                "coordinates": {"latitude": 5.350, "longitude": -4.020},
                "bounding_box": {
                    "top_left":     {"latitude": 5.357, "longitude": -4.028},
                    "bottom_right": {"latitude": 5.343, "longitude": -4.012},
                },
                "confidence": 0.96,
                "verification_status": "auto_verified",
                "facility_attributes": {
                    "estimated_footprint_sqm": 198000,
                    "visible_cooling_towers": 3,
                    "visible_stack_count": 2,
                    "transmission_lines_egressing": 4,
                    "on_site_substation_detected": True,
                },
                "change_detection": {
                    "is_new_since_last_census": False,
                    "last_census_date": "2023-01-01",
                    "construction_activity_detected": False,
                    "change_note": "No significant structural changes detected.",
                },
                "is_anchor_load": False,
                "is_generation_asset": True,
                "is_road_safety_risk": False,
                "risk_severity": None,
            },

            {
                "detection_id": "DET-003",
                "type": "port_facility",
                "subtype": "Deep Sea Container & Bulk Terminal",
                "matched_known_asset": True,
                "coordinates": {"latitude": 5.295, "longitude": -4.003},
                "bounding_box": {
                    "top_left":     {"latitude": 5.308, "longitude": -4.021},
                    "bottom_right": {"latitude": 5.282, "longitude": -3.985},
                },
                "confidence": 0.98,
                "verification_status": "auto_verified",
                "facility_attributes": {
                    "estimated_footprint_sqm": 3800000,
                    "visible_berths": 22,
                    "cranes_detected": 14,
                    "container_stacks_detected": True,
                    "on_site_substation_detected": True,
                },
                "change_detection": {
                    "is_new_since_last_census": False,
                    "last_census_date": "2023-01-01",
                    "construction_activity_detected": True,
                    "change_note": (
                        "New container terminal extension under construction "
                        "on western quay; additional crane foundations visible."
                    ),
                },
                "is_anchor_load": True,
                "is_generation_asset": False,
                "is_road_safety_risk": False,
                "risk_severity": None,
            },

            {
                "detection_id": "DET-004",
                "type": "industrial_complex",
                "subtype": "Agro-Industrial Processing Facility",
                "matched_known_asset": False,
                "coordinates": {"latitude": 5.377, "longitude": -4.195},
                "bounding_box": {
                    "top_left":     {"latitude": 5.382, "longitude": -4.201},
                    "bottom_right": {"latitude": 5.372, "longitude": -4.189},
                },
                "confidence": 0.88,
                "verification_status": "auto_verified",
                "facility_attributes": {
                    "estimated_footprint_sqm": 38000,
                    "processing_silos_detected": 4,
                    "loading_bays_detected": 6,
                    "on_site_substation_detected": False,
                    "diesel_generator_pads_detected": True,
                },
                "change_detection": {
                    "is_new_since_last_census": True,
                    "last_census_date": "2023-01-01",
                    "construction_activity_detected": False,
                    "change_note": (
                        "Facility not present in 2023 imagery. "
                        "Estimated completion Q1 2025. Identity unresolved — "
                        "forward to scan_anchor_loads for registry cross-reference."
                    ),
                },
                "is_anchor_load": True,
                "is_generation_asset": False,
                "is_road_safety_risk": False,
                "risk_severity": None,
            },

            {
                "detection_id": "DET-005",
                "type": "special_economic_zone",
                "subtype": "Export Processing Zone — Light Manufacturing",
                "matched_known_asset": True,
                "coordinates": {"latitude": 5.318, "longitude": -3.971},
                "bounding_box": {
                    "top_left":     {"latitude": 5.338, "longitude": -3.995},
                    "bottom_right": {"latitude": 5.298, "longitude": -3.947},
                },
                "confidence": 0.91,
                "verification_status": "auto_verified",
                "facility_attributes": {
                    "estimated_footprint_sqm": 9500000,
                    "estimated_built_up_pct": 58,
                    "warehouse_clusters_detected": 9,
                    "active_construction_zones": 2,
                    "internal_road_network_km": 11,
                    "on_site_substation_detected": True,
                },
                "change_detection": {
                    "is_new_since_last_census": False,
                    "last_census_date": "2023-01-01",
                    "construction_activity_detected": True,
                    "change_note": (
                        "Two new warehouse blocks under construction on north edge; "
                        "built-up area increased from 51% to 58% since 2023."
                    ),
                },
                "is_anchor_load": True,
                "is_generation_asset": False,
                "is_road_safety_risk": False,
                "risk_severity": None,
            },

            {
                "detection_id": "DET-006",
                "type": "substation",
                "subtype": "High Voltage Transmission Substation",
                "matched_known_asset": True,
                "coordinates": {"latitude": 5.362, "longitude": -4.011},
                "bounding_box": {
                    "top_left":     {"latitude": 5.366, "longitude": -4.017},
                    "bottom_right": {"latitude": 5.358, "longitude": -4.005},
                },
                "confidence": 0.93,
                "verification_status": "auto_verified",
                "facility_attributes": {
                    "estimated_footprint_sqm": 28000,
                    "transformer_bays_detected": 6,
                    "transmission_lines_egressing": 5,
                    "on_site_substation_detected": None,
                },
                "change_detection": {
                    "is_new_since_last_census": False,
                    "last_census_date": "2023-01-01",
                    "construction_activity_detected": False,
                    "change_note": "No structural changes; consistent with known grid asset.",
                },
                "is_anchor_load": False,
                "is_generation_asset": False,
                "is_road_safety_risk": False,
                "risk_severity": None,
            },

            # ── GHANA ──────────────────────────────────────────────────────

            {
                "detection_id": "DET-007",
                "type": "oil_refinery",
                "subtype": "Petroleum Refinery (Rehabilitation)",
                "matched_known_asset": True,
                "coordinates": {"latitude": 5.666, "longitude": 0.044},
                "bounding_box": {
                    "top_left":     {"latitude": 5.675, "longitude": 0.031},
                    "bottom_right": {"latitude": 5.657, "longitude": 0.057},
                },
                "confidence": 0.95,
                "verification_status": "auto_verified",
                "facility_attributes": {
                    "estimated_footprint_sqm": 1200000,
                    "visible_storage_tanks": 18,
                    "visible_processing_units": 5,
                    "transmission_lines_egressing": 2,
                    "on_site_substation_detected": True,
                    "flaring_detected": False,
                },
                "change_detection": {
                    "is_new_since_last_census": False,
                    "last_census_date": "2023-01-01",
                    "construction_activity_detected": True,
                    "change_note": (
                        "Active rehabilitation works visible — new piping runs "
                        "and scaffolding around distillation units."
                    ),
                },
                "is_anchor_load": True,
                "is_generation_asset": False,
                "is_road_safety_risk": False,
                "risk_severity": None,
            },

            {
                "detection_id": "DET-008",
                "type": "port_facility",
                "subtype": "Deep Sea Container & Bulk Terminal",
                "matched_known_asset": True,
                "coordinates": {"latitude": 5.650, "longitude": -0.018},
                "bounding_box": {
                    "top_left":     {"latitude": 5.664, "longitude": -0.033},
                    "bottom_right": {"latitude": 5.636, "longitude": -0.003},
                },
                "confidence": 0.97,
                "verification_status": "auto_verified",
                "facility_attributes": {
                    "estimated_footprint_sqm": 4200000,
                    "visible_berths": 16,
                    "cranes_detected": 10,
                    "container_stacks_detected": True,
                    "on_site_substation_detected": True,
                },
                "change_detection": {
                    "is_new_since_last_census": False,
                    "last_census_date": "2023-01-01",
                    "construction_activity_detected": True,
                    "change_note": (
                        "Expansion of container yard visible on eastern side; "
                        "new reefer plug banks installed."
                    ),
                },
                "is_anchor_load": True,
                "is_generation_asset": False,
                "is_road_safety_risk": False,
                "risk_severity": None,
            },

            {
                "detection_id": "DET-009",
                "type": "special_economic_zone",
                "subtype": "Free Trade Zone — Industrial & Manufacturing",
                "matched_known_asset": True,
                "coordinates": {"latitude": 5.650, "longitude": -0.018},
                "bounding_box": {
                    "top_left":     {"latitude": 5.668, "longitude": -0.038},
                    "bottom_right": {"latitude": 5.632, "longitude":  0.002},
                },
                "confidence": 0.94,
                "verification_status": "auto_verified",
                "facility_attributes": {
                    "estimated_footprint_sqm": 40000000,
                    "estimated_built_up_pct": 62,
                    "warehouse_clusters_detected": 21,
                    "active_construction_zones": 3,
                    "internal_road_network_km": 18,
                    "on_site_substation_detected": True,
                },
                "change_detection": {
                    "is_new_since_last_census": False,
                    "last_census_date": "2023-01-01",
                    "construction_activity_detected": True,
                    "change_note": (
                        "Three new factory shells under construction; "
                        "built-up area increased from 55% to 62% since 2023."
                    ),
                },
                "is_anchor_load": True,
                "is_generation_asset": False,
                "is_road_safety_risk": False,
                "risk_severity": None,
            },

            {
                "detection_id": "DET-010",
                "type": "hydroelectric_plant",
                "subtype": "Large-Scale Hydroelectric Dam & Reservoir",
                "matched_known_asset": True,
                "coordinates": {"latitude": 6.270, "longitude": 0.050},
                "bounding_box": {
                    "top_left":     {"latitude": 6.285, "longitude": 0.032},
                    "bottom_right": {"latitude": 6.255, "longitude": 0.068},
                },
                "confidence": 0.99,
                "verification_status": "auto_verified",
                "facility_attributes": {
                    "estimated_footprint_sqm": 850000,
                    "visible_turbine_bays": 6,
                    "dam_wall_visible": True,
                    "transmission_lines_egressing": 6,
                    "on_site_substation_detected": True,
                    "reservoir_surface_sqkm": 8480,
                },
                "change_detection": {
                    "is_new_since_last_census": False,
                    "last_census_date": "2023-01-01",
                    "construction_activity_detected": False,
                    "change_note": (
                        "Reservoir level appears lower than 2023 baseline — "
                        "consistent with seasonal variation and reduced inflows."
                    ),
                },
                "is_anchor_load": False,
                "is_generation_asset": True,
                "is_road_safety_risk": False,
                "risk_severity": None,
            },

            {
                "detection_id": "DET-011",
                "type": "solar_farm",
                "subtype": "Utility-Scale Photovoltaic Farm",
                "matched_known_asset": True,
                "coordinates": {"latitude": 4.996, "longitude": -2.788},
                "bounding_box": {
                    "top_left":     {"latitude": 5.014, "longitude": -2.811},
                    "bottom_right": {"latitude": 4.978, "longitude": -2.765},
                },
                "confidence": 0.96,
                "verification_status": "auto_verified",
                "facility_attributes": {
                    "estimated_footprint_sqm": 3100000,
                    "panel_rows_visible": True,
                    "inverter_stations_detected": 8,
                    "transmission_lines_egressing": 2,
                    "on_site_substation_detected": True,
                },
                "change_detection": {
                    "is_new_since_last_census": False,
                    "last_census_date": "2023-01-01",
                    "construction_activity_detected": True,
                    "change_note": (
                        "Additional panel arrays visible on southern perimeter — "
                        "estimated 40 MW expansion vs. 2023 imagery."
                    ),
                },
                "is_anchor_load": False,
                "is_generation_asset": True,
                "is_road_safety_risk": False,
                "risk_severity": None,
            },

            {
                "detection_id": "DET-012",
                "type": "mining_operation",
                "subtype": "Underground Gold Mine — Surface Infrastructure",
                "matched_known_asset": True,
                "coordinates": {"latitude": 6.204, "longitude": -1.672},
                "bounding_box": {
                    "top_left":     {"latitude": 6.220, "longitude": -1.692},
                    "bottom_right": {"latitude": 6.188, "longitude": -1.652},
                },
                "confidence": 0.95,
                "verification_status": "auto_verified",
                "facility_attributes": {
                    "estimated_footprint_sqm": 2800000,
                    "headframes_visible": 3,
                    "processing_plant_detected": True,
                    "tailings_pond_detected": True,
                    "on_site_substation_detected": True,
                    "transmission_lines_egressing": 2,
                    "distance_to_corridor_km": 98,
                },
                "change_detection": {
                    "is_new_since_last_census": False,
                    "last_census_date": "2023-01-01",
                    "construction_activity_detected": True,
                    "change_note": (
                        "New ventilation shaft structure visible on northern shaft; "
                        "processing plant expansion underway."
                    ),
                },
                "is_anchor_load": True,
                "is_generation_asset": False,
                "is_road_safety_risk": False,
                "risk_severity": None,
            },

            {
                "detection_id": "DET-013",
                "type": "substation",
                "subtype": "High Voltage Transmission Substation",
                "matched_known_asset": False,
                "coordinates": {"latitude": 5.658, "longitude": -0.031},
                "bounding_box": {
                    "top_left":     {"latitude": 5.663, "longitude": -0.037},
                    "bottom_right": {"latitude": 5.653, "longitude": -0.025},
                },
                "confidence": 0.61,
                "verification_status": "manual_review_required",
                "review_reason": (
                    "Confidence 0.61 — spectral signature consistent with substation "
                    "bus-bar structure, but partial obstruction by cloud shadow. "
                    "Alternative classification: large warehouse rooftop (p=0.28)."
                ),
                "facility_attributes": {
                    "estimated_footprint_sqm": 12000,
                    "transformer_bays_detected": 3,
                    "transmission_lines_egressing": 2,
                    "on_site_substation_detected": None,
                },
                "change_detection": {
                    "is_new_since_last_census": True,
                    "last_census_date": "2023-01-01",
                    "construction_activity_detected": False,
                    "change_note": (
                        "Not present in 2023 imagery — if confirmed as substation, "
                        "represents new grid infrastructure relevant to nearby "
                        "industrial zone connection."
                    ),
                },
                "is_anchor_load": False,
                "is_generation_asset": False,
                "is_road_safety_risk": False,
                "risk_severity": None,
            },

            {
                "detection_id": "DET-014",
                "type": "industrial_complex",
                "subtype": "Rice Milling & Irrigation Hub",
                "matched_known_asset": False,
                "coordinates": {"latitude": 6.032, "longitude": 0.607},
                "bounding_box": {
                    "top_left":     {"latitude": 6.041, "longitude": 0.595},
                    "bottom_right": {"latitude": 6.023, "longitude": 0.619},
                },
                "confidence": 0.83,
                "verification_status": "auto_verified",
                "facility_attributes": {
                    "estimated_footprint_sqm": 2200000,
                    "irrigated_field_area_sqm": 120000000,
                    "milling_structures_detected": 5,
                    "storage_silos_detected": 3,
                    "diesel_generator_pads_detected": True,
                    "on_site_substation_detected": False,
                },
                "change_detection": {
                    "is_new_since_last_census": False,
                    "last_census_date": "2023-01-01",
                    "construction_activity_detected": True,
                    "change_note": (
                        "Irrigated area expanded by ~8,000 ha since 2023; "
                        "new milling structure under construction on eastern edge."
                    ),
                },
                "is_anchor_load": True,
                "is_generation_asset": False,
                "is_road_safety_risk": False,
                "risk_severity": None,
            },

            {
                "detection_id": "DET-015",
                "type": "port_facility",
                "subtype": "Bulk & General Cargo Terminal",
                "matched_known_asset": True,
                "coordinates": {"latitude": 4.912, "longitude": -1.777},
                "bounding_box": {
                    "top_left":     {"latitude": 4.922, "longitude": -1.791},
                    "bottom_right": {"latitude": 4.902, "longitude": -1.763},
                },
                "confidence": 0.92,
                "verification_status": "auto_verified",
                "facility_attributes": {
                    "estimated_footprint_sqm": 980000,
                    "visible_berths": 6,
                    "cranes_detected": 3,
                    "container_stacks_detected": False,
                    "on_site_substation_detected": True,
                },
                "change_detection": {
                    "is_new_since_last_census": False,
                    "last_census_date": "2023-01-01",
                    "construction_activity_detected": True,
                    "change_note": "New liquid bulk jetty extension under construction.",
                },
                "is_anchor_load": True,
                "is_generation_asset": False,
                "is_road_safety_risk": False,
                "risk_severity": None,
            },

            {
                "detection_id": "DET-016",
                "type": "data_center",
                "subtype": "Carrier-Neutral Tier III Data Center",
                "matched_known_asset": True,
                "coordinates": {"latitude": 5.610, "longitude": -0.185},
                "bounding_box": {
                    "top_left":     {"latitude": 5.615, "longitude": -0.192},
                    "bottom_right": {"latitude": 5.605, "longitude": -0.178},
                },
                "confidence": 0.87,
                "verification_status": "auto_verified",
                "facility_attributes": {
                    "estimated_footprint_sqm": 14000,
                    "cooling_units_on_roof_detected": True,
                    "backup_generator_pads_detected": True,
                    "on_site_substation_detected": True,
                    "security_perimeter_detected": True,
                },
                "change_detection": {
                    "is_new_since_last_census": False,
                    "last_census_date": "2023-01-01",
                    "construction_activity_detected": True,
                    "change_note": (
                        "New annex building under construction adjacent to main hall; "
                        "additional generator pads visible."
                    ),
                },
                "is_anchor_load": True,
                "is_generation_asset": False,
                "is_road_safety_risk": False,
                "risk_severity": None,
            },

            # ── TOGO ───────────────────────────────────────────────────────

            {
                "detection_id": "DET-017",
                "type": "port_facility",
                "subtype": "Deep Sea Container Terminal",
                "matched_known_asset": True,
                "coordinates": {"latitude": 6.130, "longitude": 1.281},
                "bounding_box": {
                    "top_left":     {"latitude": 6.145, "longitude": 1.262},
                    "bottom_right": {"latitude": 6.115, "longitude": 1.300},
                },
                "confidence": 0.97,
                "verification_status": "auto_verified",
                "facility_attributes": {
                    "estimated_footprint_sqm": 2900000,
                    "visible_berths": 12,
                    "cranes_detected": 8,
                    "container_stacks_detected": True,
                    "on_site_substation_detected": True,
                },
                "change_detection": {
                    "is_new_since_last_census": False,
                    "last_census_date": "2023-01-01",
                    "construction_activity_detected": True,
                    "change_note": (
                        "Third container terminal berth extension in progress; "
                        "new fuel storage tanks visible on northern apron."
                    ),
                },
                "is_anchor_load": True,
                "is_generation_asset": False,
                "is_road_safety_risk": False,
                "risk_severity": None,
            },

            {
                "detection_id": "DET-018",
                "type": "thermal_power_plant",
                "subtype": "Open Cycle Gas Turbine (OCGT)",
                "matched_known_asset": True,
                "coordinates": {"latitude": 6.168, "longitude": 1.212},
                "bounding_box": {
                    "top_left":     {"latitude": 6.174, "longitude": 1.205},
                    "bottom_right": {"latitude": 6.162, "longitude": 1.219},
                },
                "confidence": 0.91,
                "verification_status": "auto_verified",
                "facility_attributes": {
                    "estimated_footprint_sqm": 62000,
                    "visible_cooling_towers": 0,
                    "visible_stack_count": 2,
                    "transmission_lines_egressing": 3,
                    "on_site_substation_detected": True,
                },
                "change_detection": {
                    "is_new_since_last_census": False,
                    "last_census_date": "2023-01-01",
                    "construction_activity_detected": False,
                    "change_note": "No structural changes detected.",
                },
                "is_anchor_load": False,
                "is_generation_asset": True,
                "is_road_safety_risk": False,
                "risk_severity": None,
            },

            {
                "detection_id": "DET-019",
                "type": "industrial_complex",
                "subtype": "Cement & Clinker Manufacturing",
                "matched_known_asset": True,
                "coordinates": {"latitude": 6.175, "longitude": 1.305},
                "bounding_box": {
                    "top_left":     {"latitude": 6.182, "longitude": 1.296},
                    "bottom_right": {"latitude": 6.168, "longitude": 1.314},
                },
                "confidence": 0.90,
                "verification_status": "auto_verified",
                "facility_attributes": {
                    "estimated_footprint_sqm": 320000,
                    "kiln_structures_detected": 2,
                    "storage_silos_detected": 6,
                    "on_site_substation_detected": True,
                    "diesel_generator_pads_detected": True,
                },
                "change_detection": {
                    "is_new_since_last_census": False,
                    "last_census_date": "2023-01-01",
                    "construction_activity_detected": False,
                    "change_note": "No structural changes detected.",
                },
                "is_anchor_load": True,
                "is_generation_asset": False,
                "is_road_safety_risk": False,
                "risk_severity": None,
            },

            {
                "detection_id": "DET-020",
                "type": "special_economic_zone",
                "subtype": "Logistics & Light Industrial Free Zone",
                "matched_known_asset": True,
                "coordinates": {"latitude": 6.195, "longitude": 1.225},
                "bounding_box": {
                    "top_left":     {"latitude": 6.209, "longitude": 1.207},
                    "bottom_right": {"latitude": 6.181, "longitude": 1.243},
                },
                "confidence": 0.89,
                "verification_status": "auto_verified",
                "facility_attributes": {
                    "estimated_footprint_sqm": 18000000,
                    "estimated_built_up_pct": 44,
                    "warehouse_clusters_detected": 12,
                    "active_construction_zones": 4,
                    "internal_road_network_km": 8,
                    "on_site_substation_detected": True,
                },
                "change_detection": {
                    "is_new_since_last_census": False,
                    "last_census_date": "2023-01-01",
                    "construction_activity_detected": True,
                    "change_note": (
                        "Built-up area increased from 36% to 44% since 2023; "
                        "four new warehouse units under construction."
                    ),
                },
                "is_anchor_load": True,
                "is_generation_asset": False,
                "is_road_safety_risk": False,
                "risk_severity": None,
            },

            # ── BENIN ──────────────────────────────────────────────────────

            {
                "detection_id": "DET-021",
                "type": "thermal_power_plant",
                "subtype": "Combined Cycle Thermal Station",
                "matched_known_asset": True,
                "coordinates": {"latitude": 6.425, "longitude": 2.406},
                "bounding_box": {
                    "top_left":     {"latitude": 6.432, "longitude": 2.396},
                    "bottom_right": {"latitude": 6.418, "longitude": 2.416},
                },
                "confidence": 0.93,
                "verification_status": "auto_verified",
                "facility_attributes": {
                    "estimated_footprint_sqm": 95000,
                    "visible_cooling_towers": 2,
                    "visible_stack_count": 2,
                    "transmission_lines_egressing": 3,
                    "on_site_substation_detected": True,
                },
                "change_detection": {
                    "is_new_since_last_census": False,
                    "last_census_date": "2023-01-01",
                    "construction_activity_detected": False,
                    "change_note": "No structural changes detected.",
                },
                "is_anchor_load": False,
                "is_generation_asset": True,
                "is_road_safety_risk": False,
                "risk_severity": None,
            },

            {
                "detection_id": "DET-022",
                "type": "port_facility",
                "subtype": "Container & Ro-Ro Terminal",
                "matched_known_asset": True,
                "coordinates": {"latitude": 6.351, "longitude": 2.435},
                "bounding_box": {
                    "top_left":     {"latitude": 6.363, "longitude": 2.418},
                    "bottom_right": {"latitude": 6.339, "longitude": 2.452},
                },
                "confidence": 0.96,
                "verification_status": "auto_verified",
                "facility_attributes": {
                    "estimated_footprint_sqm": 2100000,
                    "visible_berths": 10,
                    "cranes_detected": 5,
                    "container_stacks_detected": True,
                    "on_site_substation_detected": True,
                },
                "change_detection": {
                    "is_new_since_last_census": False,
                    "last_census_date": "2023-01-01",
                    "construction_activity_detected": True,
                    "change_note": (
                        "New ro-ro ramp and marshalling yard extension visible "
                        "on western quay."
                    ),
                },
                "is_anchor_load": True,
                "is_generation_asset": False,
                "is_road_safety_risk": False,
                "risk_severity": None,
            },

            {
                "detection_id": "DET-023",
                "type": "industrial_complex",
                "subtype": "Industrial Manufacturing Zone",
                "matched_known_asset": True,
                "coordinates": {"latitude": 6.420, "longitude": 2.391},
                "bounding_box": {
                    "top_left":     {"latitude": 6.430, "longitude": 2.378},
                    "bottom_right": {"latitude": 6.410, "longitude": 2.404},
                },
                "confidence": 0.88,
                "verification_status": "auto_verified",
                "facility_attributes": {
                    "estimated_footprint_sqm": 3000000,
                    "factory_structures_detected": 22,
                    "storage_tanks_detected": 4,
                    "on_site_substation_detected": True,
                    "diesel_generator_pads_detected": True,
                },
                "change_detection": {
                    "is_new_since_last_census": False,
                    "last_census_date": "2023-01-01",
                    "construction_activity_detected": False,
                    "change_note": "No structural changes detected.",
                },
                "is_anchor_load": True,
                "is_generation_asset": False,
                "is_road_safety_risk": False,
                "risk_severity": None,
            },

            {
                "detection_id": "DET-024",
                "type": "industrial_complex",
                "subtype": "Agro-Processing Cluster — Pineapple & Cashew",
                "matched_known_asset": False,
                "coordinates": {"latitude": 6.492, "longitude": 2.628},
                "bounding_box": {
                    "top_left":     {"latitude": 6.499, "longitude": 2.619},
                    "bottom_right": {"latitude": 6.485, "longitude": 2.637},
                },
                "confidence": 0.79,
                "verification_status": "auto_verified",
                "facility_attributes": {
                    "estimated_footprint_sqm": 45000,
                    "processing_silos_detected": 3,
                    "loading_bays_detected": 4,
                    "cold_storage_structures_detected": 2,
                    "on_site_substation_detected": False,
                    "diesel_generator_pads_detected": True,
                },
                "change_detection": {
                    "is_new_since_last_census": True,
                    "last_census_date": "2023-01-01",
                    "construction_activity_detected": False,
                    "change_note": (
                        "Facility not present in 2023 imagery. "
                        "Identity unresolved — forward to scan_anchor_loads."
                    ),
                },
                "is_anchor_load": True,
                "is_generation_asset": False,
                "is_road_safety_risk": False,
                "risk_severity": None,
            },

            {
                "detection_id": "DET-025",
                "type": "solar_farm",
                "subtype": "Utility-Scale Photovoltaic Farm",
                "matched_known_asset": False,
                "coordinates": {"latitude": 6.538, "longitude": 2.712},
                "bounding_box": {
                    "top_left":     {"latitude": 6.549, "longitude": 2.699},
                    "bottom_right": {"latitude": 6.527, "longitude": 2.725},
                },
                "confidence": 0.72,
                "verification_status": "auto_verified",
                "facility_attributes": {
                    "estimated_footprint_sqm": 680000,
                    "panel_rows_visible": True,
                    "inverter_stations_detected": 2,
                    "transmission_lines_egressing": 1,
                    "on_site_substation_detected": False,
                },
                "change_detection": {
                    "is_new_since_last_census": True,
                    "last_census_date": "2023-01-01",
                    "construction_activity_detected": True,
                    "change_note": (
                        "New solar installation — not present in 2023 imagery. "
                        "Identity unresolved — forward to scan_anchor_loads."
                    ),
                },
                "is_anchor_load": False,
                "is_generation_asset": True,
                "is_road_safety_risk": False,
                "risk_severity": None,
            },

            # ── NIGERIA ────────────────────────────────────────────────────

            {
                "detection_id": "DET-026",
                "type": "thermal_power_plant",
                "subtype": "Steam Turbine Thermal Power Station",
                "matched_known_asset": True,
                "coordinates": {"latitude": 6.563, "longitude": 3.564},
                "bounding_box": {
                    "top_left":     {"latitude": 6.572, "longitude": 3.552},
                    "bottom_right": {"latitude": 6.554, "longitude": 3.576},
                },
                "confidence": 0.97,
                "verification_status": "auto_verified",
                "facility_attributes": {
                    "estimated_footprint_sqm": 520000,
                    "visible_cooling_towers": 6,
                    "visible_stack_count": 6,
                    "transmission_lines_egressing": 5,
                    "on_site_substation_detected": True,
                },
                "change_detection": {
                    "is_new_since_last_census": False,
                    "last_census_date": "2023-01-01",
                    "construction_activity_detected": False,
                    "change_note": "No structural changes; units 3 and 4 appear mothballed.",
                },
                "is_anchor_load": False,
                "is_generation_asset": True,
                "is_road_safety_risk": False,
                "risk_severity": None,
            },

            {
                "detection_id": "DET-027",
                "type": "oil_refinery",
                "subtype": "Petroleum Refinery & Petrochemical Complex",
                "matched_known_asset": True,
                "coordinates": {"latitude": 6.438, "longitude": 3.989},
                "bounding_box": {
                    "top_left":     {"latitude": 6.452, "longitude": 3.971},
                    "bottom_right": {"latitude": 6.424, "longitude": 4.007},
                },
                "confidence": 0.99,
                "verification_status": "auto_verified",
                "facility_attributes": {
                    "estimated_footprint_sqm": 4200000,
                    "visible_storage_tanks": 48,
                    "visible_processing_units": 12,
                    "transmission_lines_egressing": 2,
                    "on_site_substation_detected": True,
                    "flaring_detected": True,
                },
                "change_detection": {
                    "is_new_since_last_census": False,
                    "last_census_date": "2023-01-01",
                    "construction_activity_detected": True,
                    "change_note": (
                        "Active commissioning activity — additional piping and "
                        "storage tanks visible vs. 2023 imagery."
                    ),
                },
                "is_anchor_load": True,
                "is_generation_asset": False,
                "is_road_safety_risk": False,
                "risk_severity": None,
            },

            {
                "detection_id": "DET-028",
                "type": "special_economic_zone",
                "subtype": "Free Trade Zone — Industrial & Manufacturing",
                "matched_known_asset": True,
                "coordinates": {"latitude": 6.427, "longitude": 3.987},
                "bounding_box": {
                    "top_left":     {"latitude": 6.471, "longitude": 3.941},
                    "bottom_right": {"latitude": 6.383, "longitude": 4.033},
                },
                "confidence": 0.98,
                "verification_status": "auto_verified",
                "facility_attributes": {
                    "estimated_footprint_sqm": 165000000,
                    "estimated_built_up_pct": 34,
                    "warehouse_clusters_detected": 18,
                    "active_construction_zones": 7,
                    "internal_road_network_km": 42,
                    "on_site_substation_detected": True,
                },
                "change_detection": {
                    "is_new_since_last_census": False,
                    "last_census_date": "2023-01-01",
                    "construction_activity_detected": True,
                    "change_note": (
                        "Significant expansion — built-up area increased from 22% "
                        "to 34% since 2023. Seven new construction zones active."
                    ),
                },
                "is_anchor_load": True,
                "is_generation_asset": False,
                "is_road_safety_risk": False,
                "risk_severity": None,
            },

            {
                "detection_id": "DET-029",
                "type": "port_facility",
                "subtype": "Deep Sea Container & Bulk Terminal",
                "matched_known_asset": True,
                "coordinates": {"latitude": 6.449, "longitude": 3.988},
                "bounding_box": {
                    "top_left":     {"latitude": 6.460, "longitude": 3.973},
                    "bottom_right": {"latitude": 6.438, "longitude": 4.003},
                },
                "confidence": 0.97,
                "verification_status": "auto_verified",
                "facility_attributes": {
                    "estimated_footprint_sqm": 1900000,
                    "visible_berths": 8,
                    "cranes_detected": 6,
                    "container_stacks_detected": True,
                    "on_site_substation_detected": True,
                },
                "change_detection": {
                    "is_new_since_last_census": True,
                    "last_census_date": "2023-01-01",
                    "construction_activity_detected": False,
                    "change_note": (
                        "Port fully operational since 2024 — not operational in "
                        "2023 census. First vessels now visible at berths."
                    ),
                },
                "is_anchor_load": True,
                "is_generation_asset": False,
                "is_road_safety_risk": False,
                "risk_severity": None,
            },

            {
                "detection_id": "DET-030",
                "type": "data_center",
                "subtype": "Carrier-Neutral Tier III/IV Data Center",
                "matched_known_asset": True,
                "coordinates": {"latitude": 6.449, "longitude": 3.988},
                "bounding_box": {
                    "top_left":     {"latitude": 6.454, "longitude": 3.982},
                    "bottom_right": {"latitude": 6.444, "longitude": 3.994},
                },
                "confidence": 0.90,
                "verification_status": "auto_verified",
                "facility_attributes": {
                    "estimated_footprint_sqm": 22000,
                    "cooling_units_on_roof_detected": True,
                    "backup_generator_pads_detected": True,
                    "on_site_substation_detected": True,
                    "security_perimeter_detected": True,
                    "fiber_entry_points_detected": 3,
                },
                "change_detection": {
                    "is_new_since_last_census": False,
                    "last_census_date": "2023-01-01",
                    "construction_activity_detected": True,
                    "change_note": (
                        "New hall extension under construction — estimated "
                        "doubling of floor space vs. 2023."
                    ),
                },
                "is_anchor_load": True,
                "is_generation_asset": False,
                "is_road_safety_risk": False,
                "risk_severity": None,
            },

            {
                "detection_id": "DET-031",
                "type": "port_facility",
                "subtype": "Multi-Purpose Port — Container & General Cargo",
                "matched_known_asset": True,
                "coordinates": {"latitude": 6.437, "longitude": 3.386},
                "bounding_box": {
                    "top_left":     {"latitude": 6.450, "longitude": 3.368},
                    "bottom_right": {"latitude": 6.424, "longitude": 3.404},
                },
                "confidence": 0.98,
                "verification_status": "auto_verified",
                "facility_attributes": {
                    "estimated_footprint_sqm": 8200000,
                    "visible_berths": 28,
                    "cranes_detected": 16,
                    "container_stacks_detected": True,
                    "on_site_substation_detected": True,
                },
                "change_detection": {
                    "is_new_since_last_census": False,
                    "last_census_date": "2023-01-01",
                    "construction_activity_detected": True,
                    "change_note": (
                        "Apapa bulk terminal rehabilitation ongoing; "
                        "new container scanning gantries installed."
                    ),
                },
                "is_anchor_load": True,
                "is_generation_asset": False,
                "is_road_safety_risk": False,
                "risk_severity": None,
            },

            {
                "detection_id": "DET-032",
                "type": "industrial_complex",
                "subtype": "Manufacturing & Logistics Cluster",
                "matched_known_asset": True,
                "coordinates": {"latitude": 6.878, "longitude": 3.662},
                "bounding_box": {
                    "top_left":     {"latitude": 6.895, "longitude": 3.641},
                    "bottom_right": {"latitude": 6.861, "longitude": 3.683},
                },
                "confidence": 0.86,
                "verification_status": "auto_verified",
                "facility_attributes": {
                    "estimated_footprint_sqm": 28000000,
                    "factory_structures_detected": 38,
                    "warehouse_clusters_detected": 12,
                    "on_site_substation_detected": True,
                    "diesel_generator_pads_detected": True,
                    "internal_road_network_km": 14,
                },
                "change_detection": {
                    "is_new_since_last_census": False,
                    "last_census_date": "2023-01-01",
                    "construction_activity_detected": True,
                    "change_note": (
                        "New pharmaceutical manufacturing block under construction "
                        "on northern perimeter."
                    ),
                },
                "is_anchor_load": True,
                "is_generation_asset": False,
                "is_road_safety_risk": False,
                "risk_severity": None,
            },

            {
                "detection_id": "DET-033",
                "type": "substation",
                "subtype": "High Voltage Transmission Substation",
                "matched_known_asset": True,
                "coordinates": {"latitude": 6.519, "longitude": 3.358},
                "bounding_box": {
                    "top_left":     {"latitude": 6.524, "longitude": 3.351},
                    "bottom_right": {"latitude": 6.514, "longitude": 3.365},
                },
                "confidence": 0.94,
                "verification_status": "auto_verified",
                "facility_attributes": {
                    "estimated_footprint_sqm": 42000,
                    "transformer_bays_detected": 8,
                    "transmission_lines_egressing": 6,
                    "on_site_substation_detected": None,
                },
                "change_detection": {
                    "is_new_since_last_census": False,
                    "last_census_date": "2023-01-01",
                    "construction_activity_detected": True,
                    "change_note": (
                        "New 330 kV transformer bank installation underway — "
                        "consistent with capacity upgrade programme."
                    ),
                },
                "is_anchor_load": False,
                "is_generation_asset": False,
                "is_road_safety_risk": False,
                "risk_severity": None,
            },

            {
                "detection_id": "DET-034",
                "type": "data_center",
                "subtype": "Hyperscale Data Center Campus",
                "matched_known_asset": False,
                "coordinates": {"latitude": 6.601, "longitude": 3.349},
                "bounding_box": {
                    "top_left":     {"latitude": 6.609, "longitude": 3.339},
                    "bottom_right": {"latitude": 6.593, "longitude": 3.359},
                },
                "confidence": 0.68,
                "verification_status": "manual_review_required",
                "review_reason": (
                    "Confidence 0.68 — large flat-roof building with rooftop cooling "
                    "consistent with data center; alternative classification: "
                    "large distribution warehouse (p=0.22). "
                    "Forward to scan_anchor_loads for registry check."
                ),
                "facility_attributes": {
                    "estimated_footprint_sqm": 55000,
                    "cooling_units_on_roof_detected": True,
                    "backup_generator_pads_detected": True,
                    "on_site_substation_detected": True,
                    "security_perimeter_detected": True,
                },
                "change_detection": {
                    "is_new_since_last_census": True,
                    "last_census_date": "2023-01-01",
                    "construction_activity_detected": False,
                    "change_note": (
                        "Not present in 2023 imagery — newly operational facility. "
                        "Identity unresolved."
                    ),
                },
                "is_anchor_load": True,
                "is_generation_asset": False,
                "is_road_safety_risk": False,
                "risk_severity": None,
            },

            {
                "detection_id": "DET-035",
                "type": "mining_operation",
                "subtype": "Lithium Exploration & Processing Site",
                "matched_known_asset": False,
                "coordinates": {"latitude": 6.812, "longitude": -1.244},
                "bounding_box": {
                    "top_left":     {"latitude": 6.824, "longitude": -1.259},
                    "bottom_right": {"latitude": 6.800, "longitude": -1.229},
                },
                "confidence": 0.71,
                "verification_status": "auto_verified",
                "facility_attributes": {
                    "estimated_footprint_sqm": 480000,
                    "open_pit_area_sqm": 120000,
                    "processing_structures_detected": 2,
                    "tailings_pond_detected": False,
                    "on_site_substation_detected": False,
                    "diesel_generator_pads_detected": True,
                    "distance_to_corridor_km": 44,
                },
                "change_detection": {
                    "is_new_since_last_census": True,
                    "last_census_date": "2023-01-01",
                    "construction_activity_detected": True,
                    "change_note": (
                        "New excavation activity and haul road visible since 2023. "
                        "Consistent with reported lithium exploration licences in area. "
                        "Identity unresolved — forward to scan_anchor_loads."
                    ),
                },
                "is_anchor_load": True,
                "is_generation_asset": False,
                "is_road_safety_risk": False,
                "risk_severity": None,
            },


            # ================================================================
            # SECTION B: ROAD SAFETY DETECTIONS (DET-RS-001 through DET-RS-010)
            # All attributes are physically observable from satellite imagery.
            # Distributed across the 5 corridor countries by risk severity.
            # ================================================================

            # ── CÔTE D'IVOIRE ─────────────────────────────────────────────

            {
                # CRITICAL — Uncontrolled junction at high-speed merge point
                # near Abidjan port approach road
                "detection_id": "DET-RS-001",
                "type": "road_safety_hazard",
                "subtype": "Uncontrolled High-Speed Junction",
                "matched_known_asset": False,
                "coordinates": {"latitude": 5.312, "longitude": -3.994},
                "bounding_box": {
                    "top_left":     {"latitude": 5.318, "longitude": -4.001},
                    "bottom_right": {"latitude": 5.306, "longitude": -3.987},
                },
                "confidence": 0.91,
                "verification_status": "auto_verified",
                "facility_attributes": {
                    "junction_arm_count": 5,
                    "traffic_light_infrastructure_detected": False,
                    "median_barrier_detected": False,
                    "sight_distance_obstruction_detected": True,
                    "highway_merge_angle_degrees": 28,
                    "heavy_vehicle_turning_radius_adequate": False,
                    "pedestrian_crossing_infrastructure_detected": False,
                    "street_lighting_detected": False,
                    "vendor_activity_in_roadway_detected": True,
                },
                "change_detection": {
                    "is_new_since_last_census": False,
                    "last_census_date": "2023-01-01",
                    "construction_activity_detected": False,
                    "change_note": (
                        "Junction geometry unchanged since 2023. Increased "
                        "surrounding commercial activity observed — higher "
                        "pedestrian and vendor encroachment than prior imagery."
                    ),
                },
                "is_anchor_load": False,
                "is_generation_asset": False,
                "is_road_safety_risk": True,
                "risk_severity": "CRITICAL",
            },

            {
                # HIGH — Roadside market on the main N1 highway corridor
                # west of Abidjan approaching Ghana border
                "detection_id": "DET-RS-002",
                "type": "road_safety_hazard",
                "subtype": "Roadside Market — High Pedestrian Density",
                "matched_known_asset": False,
                "coordinates": {"latitude": 5.339, "longitude": -3.752},
                "bounding_box": {
                    "top_left":     {"latitude": 5.345, "longitude": -3.761},
                    "bottom_right": {"latitude": 5.333, "longitude": -3.743},
                },
                "confidence": 0.87,
                "verification_status": "auto_verified",
                "facility_attributes": {
                    "estimated_footprint_sqm": 22000,
                    "market_stall_structures_detected": 63,
                    "proximity_to_carriageway_m": 8,
                    "vendor_encroachment_on_road_detected": True,
                    "informal_parking_detected": True,
                    "pedestrian_crossing_infrastructure_detected": False,
                    "street_lighting_detected": False,
                    "visible_speed_reduction_signage": False,
                    "overhead_obstruction_detected": False,
                },
                "change_detection": {
                    "is_new_since_last_census": False,
                    "last_census_date": "2023-01-01",
                    "construction_activity_detected": False,
                    "change_note": (
                        "Market footprint expanded by ~30% since 2023 — "
                        "additional stall structures encroaching further onto "
                        "road shoulder on eastern edge."
                    ),
                },
                "is_anchor_load": False,
                "is_generation_asset": False,
                "is_road_safety_risk": True,
                "risk_severity": "HIGH",
            },

            # ── GHANA ──────────────────────────────────────────────────────

            {
                # CRITICAL — Primary school directly adjacent to
                # Tema-Accra highway with no crossing or fencing
                "detection_id": "DET-RS-003",
                "type": "road_safety_hazard",
                "subtype": "School or Hospital — Road Proximity Zone",
                "matched_known_asset": False,
                "coordinates": {"latitude": 5.671, "longitude": -0.002},
                "bounding_box": {
                    "top_left":     {"latitude": 5.676, "longitude": -0.009},
                    "bottom_right": {"latitude": 5.666, "longitude":  0.005},
                },
                "confidence": 0.89,
                "verification_status": "auto_verified",
                "facility_attributes": {
                    "facility_type": "primary_school",
                    "estimated_footprint_sqm": 5800,
                    "proximity_to_carriageway_m": 6,
                    "pedestrian_crossing_detected": False,
                    "speed_bump_infrastructure_detected": False,
                    "perimeter_fencing_detected": False,
                    "school_hours_peak_risk": True,
                    "estimated_pupil_capacity": 400,
                    "street_lighting_detected": False,
                },
                "change_detection": {
                    "is_new_since_last_census": False,
                    "last_census_date": "2023-01-01",
                    "construction_activity_detected": True,
                    "change_note": (
                        "New classroom block under construction on road-facing side — "
                        "will reduce already minimal setback distance from carriageway."
                    ),
                },
                "is_anchor_load": False,
                "is_generation_asset": False,
                "is_road_safety_risk": True,
                "risk_severity": "CRITICAL",
            },

            {
                # HIGH — Informal settlement encroaching on highway
                # shoulder between Tema and Accra
                "detection_id": "DET-RS-004",
                "type": "road_safety_hazard",
                "subtype": "Informal Settlement — Road Edge Encroachment",
                "matched_known_asset": False,
                "coordinates": {"latitude": 5.689, "longitude": 0.071},
                "bounding_box": {
                    "top_left":     {"latitude": 5.698, "longitude": 0.059},
                    "bottom_right": {"latitude": 5.680, "longitude": 0.083},
                },
                "confidence": 0.85,
                "verification_status": "auto_verified",
                "facility_attributes": {
                    "estimated_footprint_sqm": 41000,
                    "structure_count_detected": 112,
                    "proximity_to_carriageway_m": 3,
                    "footpath_infrastructure_detected": False,
                    "estimated_population_density": "very_high",
                    "night_lighting_detected": False,
                    "drainage_channel_blocking_road_detected": True,
                },
                "change_detection": {
                    "is_new_since_last_census": False,
                    "last_census_date": "2023-01-01",
                    "construction_activity_detected": True,
                    "change_note": (
                        "Settlement footprint expanded by ~25% since 2023; "
                        "new structures now within 3m of carriageway edge on "
                        "western section — closer than 2023 baseline of 8m."
                    ),
                },
                "is_anchor_load": False,
                "is_generation_asset": False,
                "is_road_safety_risk": True,
                "risk_severity": "HIGH",
            },

            {
                # MEDIUM — Unsignalised fuel station entry/exit
                # on high-speed section near Takoradi
                "detection_id": "DET-RS-005",
                "type": "road_safety_hazard",
                "subtype": "Fuel Station — Unsignalised Entry/Exit",
                "matched_known_asset": False,
                "coordinates": {"latitude": 4.931, "longitude": -1.762},
                "bounding_box": {
                    "top_left":     {"latitude": 4.935, "longitude": -1.768},
                    "bottom_right": {"latitude": 4.927, "longitude": -1.756},
                },
                "confidence": 0.82,
                "verification_status": "auto_verified",
                "facility_attributes": {
                    "estimated_footprint_sqm": 3200,
                    "pump_bays_detected": 8,
                    "deceleration_lane_detected": False,
                    "acceleration_lane_detected": False,
                    "proximity_to_junction_m": 38,
                    "entry_exit_points": 3,
                    "informal_parking_on_carriageway_detected": True,
                    "visible_speed_reduction_signage": False,
                },
                "change_detection": {
                    "is_new_since_last_census": False,
                    "last_census_date": "2023-01-01",
                    "construction_activity_detected": True,
                    "change_note": (
                        "Additional pump bays added on road-facing side since 2023 — "
                        "increasing vehicle turning movements onto highway."
                    ),
                },
                "is_anchor_load": False,
                "is_generation_asset": False,
                "is_road_safety_risk": True,
                "risk_severity": "MEDIUM",
            },

            # ── TOGO ───────────────────────────────────────────────────────

            {
                # CRITICAL — Border crossing with extreme congestion
                # and uncontrolled pedestrian mixing with heavy vehicles
                "detection_id": "DET-RS-006",
                "type": "road_safety_hazard",
                "subtype": "Border Crossing — Congestion & Pedestrian Mix Zone",
                "matched_known_asset": False,
                "coordinates": {"latitude": 6.101, "longitude": 1.194},
                "bounding_box": {
                    "top_left":     {"latitude": 6.110, "longitude": 1.183},
                    "bottom_right": {"latitude": 6.092, "longitude": 1.205},
                },
                "confidence": 0.93,
                "verification_status": "auto_verified",
                "facility_attributes": {
                    "estimated_queue_length_m": 820,
                    "estimated_queued_vehicles": 145,
                    "pedestrian_informal_crossing_detected": True,
                    "formal_crossing_infrastructure_detected": False,
                    "vendor_activity_in_roadway_detected": True,
                    "lighting_detected": False,
                    "avg_vehicle_dwell_time_hours_estimated": 8,
                    "median_barrier_in_queue_zone_detected": False,
                    "emergency_vehicle_access_lane_detected": False,
                },
                "change_detection": {
                    "is_new_since_last_census": False,
                    "last_census_date": "2023-01-01",
                    "construction_activity_detected": False,
                    "change_note": (
                        "Queue length increased significantly vs. 2023 imagery — "
                        "consistent with higher trade volumes post-AfCFTA. "
                        "No improvement in crossing infrastructure observed."
                    ),
                },
                "is_anchor_load": False,
                "is_generation_asset": False,
                "is_road_safety_risk": True,
                "risk_severity": "CRITICAL",
            },

            {
                # MEDIUM — Livestock crossing zone on rural section
                # between Lomé and Cotonou during dry-season migration
                "detection_id": "DET-RS-007",
                "type": "road_safety_hazard",
                "subtype": "Livestock & Agricultural Crossing Zone",
                "matched_known_asset": False,
                "coordinates": {"latitude": 6.248, "longitude": 1.612},
                "bounding_box": {
                    "top_left":     {"latitude": 6.257, "longitude": 1.601},
                    "bottom_right": {"latitude": 6.239, "longitude": 1.623},
                },
                "confidence": 0.77,
                "verification_status": "auto_verified",
                "facility_attributes": {
                    "grazing_land_proximity_m": 18,
                    "formal_livestock_crossing_detected": False,
                    "fencing_along_carriageway_detected": False,
                    "seasonal_risk": True,
                    "seasonal_peak": "dry_season_migration",
                    "herder_track_crossing_road_detected": True,
                    "warning_signage_detected": False,
                },
                "change_detection": {
                    "is_new_since_last_census": False,
                    "last_census_date": "2023-01-01",
                    "construction_activity_detected": False,
                    "change_note": (
                        "Grazing land extent unchanged. No safety improvements "
                        "observed. Herder tracks remain active across carriageway."
                    ),
                },
                "is_anchor_load": False,
                "is_generation_asset": False,
                "is_road_safety_risk": True,
                "risk_severity": "MEDIUM",
            },

            # ── BENIN ──────────────────────────────────────────────────────

            {
                # HIGH — Sharp curve on elevated section approaching
                # Cotonou with no guardrail and vegetation obstruction
                "detection_id": "DET-RS-008",
                "type": "road_safety_hazard",
                "subtype": "Sharp Curve — Limited Sight Distance",
                "matched_known_asset": False,
                "coordinates": {"latitude": 6.368, "longitude": 2.461},
                "bounding_box": {
                    "top_left":     {"latitude": 6.375, "longitude": 2.453},
                    "bottom_right": {"latitude": 6.361, "longitude": 2.469},
                },
                "confidence": 0.84,
                "verification_status": "auto_verified",
                "facility_attributes": {
                    "curve_radius_estimated_m": 72,
                    "elevation_change_m": 18,
                    "guardrail_detected": False,
                    "warning_signage_detected": False,
                    "vegetation_obstruction_detected": True,
                    "avg_corridor_speed_zone_kmh": 100,
                    "opposing_carriageway_visible_from_apex": False,
                    "road_surface_condition_visible": "deteriorated",
                },
                "change_detection": {
                    "is_new_since_last_census": False,
                    "last_census_date": "2023-01-01",
                    "construction_activity_detected": False,
                    "change_note": (
                        "Vegetation obstruction has increased since 2023 — "
                        "tree canopy now overhangs curve apex, further reducing "
                        "sight distance. Road surface deterioration visible."
                    ),
                },
                "is_anchor_load": False,
                "is_generation_asset": False,
                "is_road_safety_risk": True,
                "risk_severity": "HIGH",
            },

            # ── NIGERIA ────────────────────────────────────────────────────

            {
                # HIGH — Informal truck layby on Lagos-Benin expressway
                # with carriageway encroachment and no lighting
                "detection_id": "DET-RS-009",
                "type": "road_safety_hazard",
                "subtype": "Truck Layby — Informal Roadside Parking",
                "matched_known_asset": False,
                "coordinates": {"latitude": 6.502, "longitude": 3.291},
                "bounding_box": {
                    "top_left":     {"latitude": 6.509, "longitude": 3.281},
                    "bottom_right": {"latitude": 6.495, "longitude": 3.301},
                },
                "confidence": 0.88,
                "verification_status": "auto_verified",
                "facility_attributes": {
                    "estimated_parked_vehicles": 34,
                    "formal_rest_area_infrastructure_detected": False,
                    "encroachment_on_carriageway_detected": True,
                    "encroachment_width_estimated_m": 2.4,
                    "proximity_to_bend_m": 95,
                    "lighting_detected": False,
                    "fuel_hawking_activity_detected": True,
                    "truck_maintenance_activity_in_road_detected": True,
                },
                "change_detection": {
                    "is_new_since_last_census": False,
                    "last_census_date": "2023-01-01",
                    "construction_activity_detected": False,
                    "change_note": (
                        "Layby occupancy has grown significantly — "
                        "estimated 34 trucks vs. 18 in 2023 imagery. "
                        "Carriageway encroachment now clearly visible."
                    ),
                },
                "is_anchor_load": False,
                "is_generation_asset": False,
                "is_road_safety_risk": True,
                "risk_severity": "HIGH",
            },

            {
                # LOW — Active road works on Lagos ring road section
                # with minimal temporary safety infrastructure
                "detection_id": "DET-RS-010",
                "type": "road_safety_hazard",
                "subtype": "Road Works — Active Construction Zone",
                "matched_known_asset": False,
                "coordinates": {"latitude": 6.548, "longitude": 3.328},
                "bounding_box": {
                    "top_left":     {"latitude": 6.554, "longitude": 3.319},
                    "bottom_right": {"latitude": 6.542, "longitude": 3.337},
                },
                "confidence": 0.91,
                "verification_status": "auto_verified",
                "facility_attributes": {
                    "affected_length_km": 3.1,
                    "lane_reduction_detected": True,
                    "lanes_reduced_from": 3,
                    "lanes_reduced_to": 1,
                    "temporary_signage_detected": False,
                    "construction_equipment_count": 11,
                    "proximity_to_settlement_m": 180,
                    "traffic_marshal_positions_detected": False,
                    "night_lighting_on_works_detected": False,
                },
                "change_detection": {
                    "is_new_since_last_census": True,
                    "last_census_date": "2023-01-01",
                    "construction_activity_detected": True,
                    "change_note": (
                        "Road works not present in 2023 imagery — commenced "
                        "approximately Q3 2025 based on imagery timeline. "
                        "Works extend 3.1 km with single-lane contraflow."
                    ),
                },
                "is_anchor_load": False,
                "is_generation_asset": False,
                "is_road_safety_risk": True,
                "risk_severity": "LOW",
            },

        ],  # end detections

        # ------------------------------------------------------------------ #
        #  SUMMARY                                                            #
        # ------------------------------------------------------------------ #
        "summary": {
            "total_detections": 45,
            "detections_shown_in_sample": 45,
            "auto_verified": 40,
            "manual_review_required": 3,
            "new_since_last_census": 12,
            "outside_corridor_boundary_excluded": 0,
            "by_type": {
                # — Energy & Economic Infrastructure —
                "thermal_power_plant": 4,
                "hydroelectric_plant": 1,
                "solar_farm": 3,
                "oil_refinery": 2,
                "port_facility": 7,
                "special_economic_zone": 4,
                "industrial_complex": 9,
                "substation": 5,
                "data_center": 4,
                "mining_operation": 3,
                # — Road Safety —
                "road_safety_hazard": 10,
            },
            "anchor_loads_identified": {
                "total": 45,
                "critical_priority": 8,
                "high_priority": 14,
                "medium_priority": 18,
                "pending_verification": 5,
            },
            "generation_assets_identified": 10,
            "road_safety_hazards_identified": {
                "total": 10,
                "by_severity": {
                    "CRITICAL": 3,
                    "HIGH": 4,
                    "MEDIUM": 2,
                    "LOW": 1,
                },
                "by_subtype": {
                    "Uncontrolled High-Speed Junction": 1,
                    "Roadside Market — High Pedestrian Density": 1,
                    "School or Hospital — Road Proximity Zone": 1,
                    "Informal Settlement — Road Edge Encroachment": 1,
                    "Fuel Station — Unsignalised Entry/Exit": 1,
                    "Border Crossing — Congestion & Pedestrian Mix Zone": 1,
                    "Livestock & Agricultural Crossing Zone": 1,
                    "Sharp Curve — Limited Sight Distance": 1,
                    "Truck Layby — Informal Roadside Parking": 1,
                    "Road Works — Active Construction Zone": 1,
                },
                "by_country": {
                    "Cote d'Ivoire": 2,
                    "Ghana": 2,
                    "Togo": 2,
                    "Benin": 1,
                    "Nigeria": 2,
                },
                "critical_hazards_requiring_immediate_design_response": [
                    "DET-RS-001: Uncontrolled 5-arm junction near Abidjan port approach — no signals, no median, vendor encroachment",
                    "DET-RS-003: Primary school 6m from carriageway near Tema — no crossing, no fence, expansion worsening setback",
                    "DET-RS-006: Ghana-Togo border crossing — 820m queue, 145 vehicles, pedestrians mixing with HGVs at night",
                ],
                "note": (
                    "All road safety attributes are physically observable from "
                    "10m Sentinel-2 satellite imagery. Severity ratings are "
                    "based on proximity to carriageway, missing safety infrastructure, "
                    "and visible hazard density. Detailed design mitigation recommendations "
                    "are handled downstream by the Infrastructure Optimization Agent."
                ),
            },
            "notable_new_discoveries": [
                # — Infrastructure —
                "DET-004: Unregistered agro-processing facility — not in any known registry",
                "DET-013: Possible new HV substation near Tema industrial area — manual review required",
                "DET-024: New agro-processing cluster in Benin — identity unresolved",
                "DET-025: New solar farm in Benin — identity unresolved",
                "DET-029: Lekki Deep Sea Port now fully operational — first appeared 2024",
                "DET-034: Possible hyperscale data center in Lagos — manual review required",
                "DET-035: Lithium exploration site in Ghana — identity unresolved",
                "3 new warehouse clusters detected in Cotonou Port Zone",
                "Solar expansion visible at Ghana west-coast site vs. 2023 imagery",
                # — Road Safety —
                "DET-RS-002: Roadside market stall encroachment increased 30% since 2023 on N1 highway",
                "DET-RS-004: Informal settlement now within 3m of carriageway near Tema — worsened from 8m in 2023",
                "DET-RS-009: Truck layby occupancy nearly doubled since 2023 on Lagos-Benin expressway",
                "DET-RS-010: New active road works commenced Q3 2025 — 3.1 km single-lane contraflow, no signage",
            ],
            "note": (
                "Detections are split into two sections: "
                "(A) Energy & Economic Infrastructure (DET-001 to DET-035) and "
                "(B) Road Safety Hazards (DET-RS-001 to DET-RS-010). "
                "Fields for company name, MW demand, off-take quality, load profile, "
                "and buildout demand are intentionally absent from Section A — "
                "these are resolved by downstream Opportunity Identification Agent tools: "
                "scan_anchor_loads, calculate_current_demand, assess_bankability, "
                "and model_growth_trajectory respectively. "
                "Road safety mitigation recommendations are handled by the "
                "Infrastructure Optimization Agent."
            ),
        },

        "output_uris": {
            "detections_geojson": (
                "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                "detections/infrastructure_detections.geojson"
            ),
            "bounding_boxes_overlay": (
                "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                "detections/bbox_overlay.tif"
            ),
            "manual_review_tiles": (
                "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                "detections/manual_review_tiles/"
            ),
            "anchor_load_list_geojson": (
                "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                "detections/anchor_loads_only.geojson"
            ),
            "generation_assets_geojson": (
                "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                "detections/generation_assets_only.geojson"
            ),
            # — New Road Safety Output URIs —
            "road_safety_hazards_geojson": (
                "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                "detections/road_safety_hazards.geojson"
            ),
            "road_safety_heatmap_raster": (
                "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                "detections/road_safety_heatmap.tif"
            ),
            "critical_hazards_geojson": (
                "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                "detections/critical_hazards_only.geojson"
            ),
        },
    }

    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=json.dumps(response),
                    tool_call_id=runtime.tool_call_id,
                )
            ]
        }
    )