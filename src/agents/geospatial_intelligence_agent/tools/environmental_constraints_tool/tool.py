import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import EnvironmentalInput


@tool("environmental_constraints", description=TOOL_DESCRIPTION)
def environmental_constraints_tool(
    payload: EnvironmentalInput, runtime: ToolRuntime
) -> Command:
    """
    Identifies legal, environmental, and human safety 'No-Go' and
    'Mitigation-Required' zones by checking overlap between the corridor
    and protected area databases, AND human exposure risk zones derived
    from road safety detections.

    Two constraint categories are assessed:

    ENVIRONMENTAL CONSTRAINTS (existing):
    - Protected areas (IUCN categories I-VI)
    - Wetlands and Ramsar sites
    - Cultural heritage sites
    → Standards: IFC PS6, World Bank OP 4.04, OP 4.11, AfDB ISS

    HUMAN SAFETY CONSTRAINTS (new):
    - School and hospital proximity zones
    - Dense settlement encroachment zones
    - High-pedestrian market zones
    - Border crossing congestion zones
    - Uncontrolled junction zones
    → Standards: IFC PS2, World Bank ESS4 (Community Health & Safety),
      WHO Road Safety Manual, ECOWAS Road Safety Policy Framework

    In a real-world scenario, this tool would:
    1. Load vector data (GeoJSON/Shapefile) from Tool 3.
    2. Perform spatial joins between corridor and protected/hazard polygons.
    3. Apply buffers (500m environmental, 200m safety) to detected zones.
    4. Query IUCN Red List, UNESCO, and OSM POI records.
    5. Cross-reference road safety detections from infrastructure_detection tool.
    """

    response = {
        "audit_metadata": {
            "tool": "environmental_constraints",
            "corridor_id": "ABIDJAN_LAGOS_CORRIDOR",
            "source_layers": {
                "protected_areas": (
                    "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                    "vectors/wdpa_protected_areas.geojson"
                ),
                "admin_boundaries": (
                    "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                    "vectors/gadm41_admin_boundaries.geojson"
                ),
                "road_safety_detections": (
                    "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                    "detections/road_safety_hazards.geojson"
                ),
                "osm_points_of_interest": (
                    "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                    "vectors/osm_poi_corridor.geojson"
                ),
                "population_density": (
                    "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                    "rasters/worldpop_2025_100m.tif"
                ),
            },
            "buffer_applied_m": {
                "environmental": 500,
                "human_safety": 200,
            },
            "standards_applied": [
                # — Environmental —
                "IFC Performance Standard 6 (Biodiversity Conservation)",
                "World Bank OP 4.04 (Natural Habitats)",
                "World Bank OP 4.11 (Physical Cultural Resources)",
                "AfDB Integrated Safeguards System (ISS) — Category 1 trigger check",
                "ECOWAS Environmental Policy Framework",
                # — Human Safety —
                "IFC Performance Standard 2 (Labour & Working Conditions)",
                "World Bank ESS4 (Community Health, Safety and Security)",
                "WHO Road Safety Manual for Decision-Makers (2013)",
                "ECOWAS Road Safety Policy Framework 2011–2020",
                "African Road Safety Action Plan 2011–2020 (AU/UNECA)",
            ],
            "generated_at": "2026-01-26T09:22:11+00:00",
            "total_corridor_area_sqkm": 102430.0,
        },

        "status": "Environmental & Safety Audit Complete — Conflicts Detected",
        "overall_risk_rating": "Moderate-High",
        "requires_esia": True,
        "esia_category": "Category A (Full ESIA Required)",
        "esia_rationale": (
            "3 IUCN Category I–II protected areas intersect corridor buffer. "
            "3 CRITICAL human safety zones identified requiring mandatory design "
            "mitigation. Triggers mandatory full Environmental and Social Impact "
            "Assessment under AfDB ISS, IFC PS6, and World Bank ESS4."
        ),

        # ================================================================
        # SECTION A: ENVIRONMENTAL CONSTRAINTS (original — unchanged)
        # ================================================================

        "protected_area_conflicts": [
            {
                "conflict_id": "ENV-001",
                "name": "Ankasa Conservation Area",
                "country": "Ghana",
                "iucn_category": "II (National Park)",
                "wdpa_id": "2188",
                "risk_level": "Critical",
                "legal_basis": (
                    "Ghana Wildlife Conservation Regulations 1971 (LI 685); "
                    "IFC PS6 No-Go Zone"
                ),
                "conflict_type": "Direct Overlap",
                "overlap_with_corridor_buffer_sqkm": 48.3,
                "overlap_pct_of_protected_area": 9.5,
                "centroid": {"latitude": 5.271, "longitude": -2.694},
                "recommended_action": (
                    "HARD RE-ROUTE — transmission line must pass minimum 500m "
                    "outside park boundary. Northern detour of ~14 km required."
                ),
                "detour_cost_estimate_usd": 8400000,
                "permitting_outlook": (
                    "Permit will not be granted through core zone. "
                    "Re-route is the only compliant path."
                ),
                "notes": (
                    "Ankasa is a globally significant rainforest fragment. Any "
                    "encroachment will trigger IFC PS6 critical habitat provisions "
                    "and likely disqualify DFI financing."
                ),
            },
            {
                "conflict_id": "ENV-002",
                "name": "Nzema Forest Reserve",
                "country": "Ghana",
                "iucn_category": "VI (Protected Area with Sustainable Use)",
                "wdpa_id": "34759",
                "risk_level": "High",
                "legal_basis": (
                    "Ghana Forest and Wildlife Policy 2012; World Bank OP 4.04"
                ),
                "conflict_type": "Buffer Zone Overlap",
                "overlap_with_corridor_buffer_sqkm": 22.7,
                "overlap_pct_of_protected_area": 12.4,
                "centroid": {"latitude": 4.996, "longitude": -2.788},
                "recommended_action": (
                    "RE-ROUTE or negotiate Right-of-Way with Forestry Commission "
                    "of Ghana. IUCN Category VI allows limited infrastructure with "
                    "mitigation. Minimum 500m setback from core zone boundary."
                ),
                "detour_cost_estimate_usd": 4200000,
                "permitting_outlook": (
                    "Conditional permit possible (Category VI) — requires Forestry "
                    "Commission approval, biodiversity offset plan, and community "
                    "benefit-sharing agreement."
                ),
                "notes": (
                    "Route deviation of ~8 km northward resolves conflict. If ROW "
                    "negotiated through buffer zone, a Biodiversity Management Plan "
                    "and annual monitoring will be required conditions of DFI financing."
                ),
            },
            {
                "conflict_id": "ENV-003",
                "name": "Omo Forest Reserve",
                "country": "Nigeria",
                "iucn_category": "IV (Habitat/Species Management Area)",
                "wdpa_id": "15588",
                "risk_level": "High",
                "legal_basis": (
                    "Nigeria Forestry Act Cap F34 LFN 2004; AfDB ISS Category 1"
                ),
                "conflict_type": "Direct Overlap",
                "overlap_with_corridor_buffer_sqkm": 31.9,
                "overlap_pct_of_protected_area": 6.8,
                "centroid": {"latitude": 6.718, "longitude": 4.352},
                "recommended_action": (
                    "RE-ROUTE eastern approach — shift corridor 6 km south to avoid "
                    "reserve boundary. Coordinate with Nigeria Forestry Research "
                    "Institute (FRIN)."
                ),
                "detour_cost_estimate_usd": 5600000,
                "permitting_outlook": (
                    "Permit theoretically possible under IUCN Category IV, but Nigeria "
                    "FRIN has historically refused infrastructure ROW in Omo. Re-route "
                    "strongly recommended to avoid 18–24 month permitting delay."
                ),
                "notes": (
                    "Omo is Nigeria's largest lowland rainforest and a biodiversity "
                    "hotspot. Attempting to route through reserve will trigger Category A "
                    "ESIA escalation and delay financial close."
                ),
            },
            {
                "conflict_id": "ENV-004",
                "name": "Lekki Conservation Centre",
                "country": "Nigeria",
                "iucn_category": "IV (Habitat/Species Management Area)",
                "wdpa_id": "555628185",
                "risk_level": "Medium",
                "legal_basis": (
                    "Lagos State Urban Planning Law 2010; NCS Conservation Policy"
                ),
                "conflict_type": "Buffer Zone Overlap",
                "overlap_with_corridor_buffer_sqkm": 4.1,
                "overlap_pct_of_protected_area": 5.2,
                "centroid": {"latitude": 6.452, "longitude": 3.558},
                "recommended_action": (
                    "Underground cable recommended through 3.8 km section adjacent "
                    "to reserve. Avoids aerial ROW conflict and visual impact on "
                    "protected wetland."
                ),
                "detour_cost_estimate_usd": 2800000,
                "permitting_outlook": (
                    "Permit likely obtainable with underground cable commitment and "
                    "NCS consultation. Lower risk than ENV-001 through ENV-003."
                ),
                "notes": (
                    "Key constraint for Lagos terminal segment design. Underground "
                    "XLPE cable adds ~$2.8M but resolves conflict and aligns with "
                    "Lagos State green corridor policy."
                ),
            },
        ],

        "wetland_and_water_body_conflicts": [
            {
                "conflict_id": "WET-001",
                "name": "Keta Lagoon Ramsar Site",
                "country": "Ghana",
                "designation": "Ramsar Wetland of International Importance",
                "ramsar_site_no": "1000",
                "risk_level": "Critical",
                "conflict_type": "Direct Overlap",
                "overlap_sqkm": 6.8,
                "recommended_action": (
                    "No towers within Ramsar boundary. Route must pass north of "
                    "lagoon. Elevated pile-supported structure required for any "
                    "crossing of tidal channels."
                ),
                "permitting_outlook": (
                    "Ramsar Convention Article 3.2 — any works within site require "
                    "notification to Ramsar Secretariat. Ghana EPA will require "
                    "full aquatic ESIA."
                ),
                "notes": (
                    "Ramsar designation creates international treaty obligation. "
                    "IFC PS6 triggers for natural habitat. This is the single "
                    "highest-risk environmental constraint on the corridor."
                ),
            },
            {
                "conflict_id": "WET-002",
                "name": "Volta River Mouth & Delta",
                "country": "Ghana",
                "designation": "Nationally Protected Wetland",
                "risk_level": "High",
                "conflict_type": "Direct Overlap",
                "overlap_sqkm": 11.4,
                "recommended_action": (
                    "Transmission crossing must use elevated structures (not "
                    "underwater cable) to allow river navigation. Environmental "
                    "Flow Assessment required. Coordinate with Volta River "
                    "Authority (VRA)."
                ),
                "permitting_outlook": (
                    "Crossable with standard river crossing methodology. VRA permit "
                    "and EPA Ghana Environmental Permit required "
                    "(estimated 9–12 month process)."
                ),
                "notes": (
                    "Volta River Authority has existing transmission crossing "
                    "experience — early engagement recommended to leverage "
                    "existing permitting precedent."
                ),
            },
        ],

        "cultural_heritage_conflicts": [
            {
                "conflict_id": "CHR-001",
                "name": "Asante Traditional Buildings — Kumasi Buffer Zone",
                "country": "Ghana",
                "designation": "UNESCO World Heritage Site Buffer Zone",
                "risk_level": "Medium",
                "conflict_type": "Buffer Zone Proximity",
                "distance_to_heritage_boundary_m": 1840,
                "recommended_action": (
                    "Maintain minimum 2 km setback from UNESCO buffer boundary. "
                    "Conduct archaeological survey of 500m corridor strip per "
                    "World Bank OP 4.11."
                ),
                "permitting_outlook": (
                    "No direct overlap — manageable with standard archaeological "
                    "chance-finds protocol and setback compliance."
                ),
                "notes": (
                    "Transmission line does not need to pass near Kumasi core zone. "
                    "Current proposed routing maintains adequate separation."
                ),
            },
        ],

        # ================================================================
        # SECTION B: HUMAN SAFETY CONSTRAINTS (new)
        # Sourced from road safety detections (DET-RS-001 to DET-RS-010).
        # Treated equivalently to environmental constraints for routing
        # and CAPEX purposes under World Bank ESS4.
        # ================================================================

        "human_safety_conflicts": [

            # ── CRITICAL ──────────────────────────────────────────────────

            {
                "conflict_id": "HSC-001",
                "source_detection": "DET-RS-001",
                "name": "Uncontrolled 5-Arm Junction — Abidjan Port Approach",
                "country": "Cote d'Ivoire",
                "subtype": "Uncontrolled High-Speed Junction",
                "risk_level": "CRITICAL",
                "legal_basis": (
                    "World Bank ESS4 (Community Health, Safety and Security); "
                    "Côte d'Ivoire Highway Code (Code de la Route) Art. 78–82; "
                    "WHO Road Safety Manual Chapter 4"
                ),
                "conflict_type": "Direct Design Conflict",
                "coordinates": {"latitude": 5.312, "longitude": -3.994},
                "buffer_zone_m": 200,
                "affected_road_length_m": 450,
                "key_hazard_indicators": {
                    "junction_arm_count": 5,
                    "traffic_light_infrastructure_detected": False,
                    "median_barrier_detected": False,
                    "sight_distance_obstruction_detected": True,
                    "vendor_activity_in_roadway_detected": True,
                    "heavy_vehicle_turning_radius_adequate": False,
                },
                "estimated_affected_population": 8400,
                "recommended_action": (
                    "MANDATORY DESIGN INTERVENTION before construction. "
                    "Re-engineer junction to signalised roundabout with "
                    "dedicated HGV turning lanes, raised median, vendor "
                    "relocation zone, and formal pedestrian crossing. "
                    "Cannot be deferred to post-construction phase."
                ),
                "required_mitigation": [
                    "Signalised roundabout with HGV-rated geometry",
                    "Raised median barrier on approach roads (200m each arm)",
                    "Formal pedestrian crossing with refuge islands",
                    "Vendor relocation to designated off-road trading zone",
                    "LED street lighting on all 5 arms",
                    "Variable message speed warning signs on approach",
                ],
                "mitigation_capex_estimated_usd": 3500000,
                "permitting_outlook": (
                    "Mandatory under ESS4 — DFI financing conditionality. "
                    "Côte d'Ivoire Ministry of Transport sign-off required. "
                    "Estimated 4–6 month design and approval process."
                ),
                "dfI_financing_impact": (
                    "Unmitigated junction will trigger ESS4 non-compliance "
                    "finding during DFI appraisal. Financial close cannot "
                    "proceed without approved mitigation design."
                ),
                "notes": (
                    "Port approach traffic volume makes this junction one of the "
                    "highest-risk points on the entire corridor. Increasing port "
                    "expansion activity (DET-003) will further compound risk "
                    "if junction is not redesigned before corridor opens."
                ),
            },

            {
                "conflict_id": "HSC-002",
                "source_detection": "DET-RS-003",
                "name": "Primary School — Direct Carriageway Adjacency, Tema",
                "country": "Ghana",
                "subtype": "School — Road Proximity Zone",
                "risk_level": "CRITICAL",
                "legal_basis": (
                    "World Bank ESS4 (Community Health, Safety and Security); "
                    "Ghana Road Safety Authority Act 567 (1999); "
                    "Ghana Education Service School Siting Guidelines"
                ),
                "conflict_type": "Direct Human Exposure Conflict",
                "coordinates": {"latitude": 5.671, "longitude": -0.002},
                "buffer_zone_m": 200,
                "affected_road_length_m": 280,
                "key_hazard_indicators": {
                    "proximity_to_carriageway_m": 6,
                    "pedestrian_crossing_detected": False,
                    "speed_bump_infrastructure_detected": False,
                    "perimeter_fencing_detected": False,
                    "school_hours_peak_risk": True,
                    "estimated_pupil_capacity": 400,
                    "new_construction_worsening_setback": True,
                },
                "estimated_affected_population": 400,
                "recommended_action": (
                    "MANDATORY DESIGN INTERVENTION. Install raised pedestrian "
                    "crossing with traffic signals timed to school hours, "
                    "speed tables 50m either side of school boundary, "
                    "perimeter safety fencing, and school zone signage. "
                    "Halt new classroom construction on road-facing side "
                    "pending safety assessment."
                ),
                "required_mitigation": [
                    "Signalised raised pedestrian crossing (school hours activation)",
                    "Speed tables — 2 units, 50m approach each side",
                    "Perimeter safety fencing — full school boundary (200m)",
                    "School zone warning signage — 150m advance each direction",
                    "LED street lighting covering crossing and school frontage",
                    "20 km/h school zone speed limit with enforcement camera",
                    "Construction halt order — road-facing classroom block",
                ],
                "mitigation_capex_estimated_usd": 850000,
                "permitting_outlook": (
                    "Ghana Road Safety Authority (NRSA) approval required. "
                    "Construction halt order requires Ghana Education Service "
                    "coordination. Estimated 3–4 month process."
                ),
                "dfI_financing_impact": (
                    "School proximity within 10m of carriageway is a Category A "
                    "ESS4 trigger. World Bank and AfDB appraisal teams will "
                    "flag this as a prior action — mitigation design must be "
                    "approved before financing negotiations proceed."
                ),
                "notes": (
                    "New classroom construction detected in 2025 imagery will "
                    "further reduce the already inadequate 6m setback. "
                    "Urgent engagement with Ghana Education Service required "
                    "to halt construction until safety design is approved. "
                    "This is the highest child safety risk on the corridor."
                ),
            },

            {
                "conflict_id": "HSC-003",
                "source_detection": "DET-RS-006",
                "name": "Ghana-Togo Border Crossing — Pedestrian-HGV Conflict Zone",
                "country": "Togo",
                "subtype": "Border Crossing — Congestion & Pedestrian Mix Zone",
                "risk_level": "CRITICAL",
                "legal_basis": (
                    "World Bank ESS4 (Community Health, Safety and Security); "
                    "ECOWAS Road Safety Policy Framework Art. 12; "
                    "Togo Code de la Sécurité Routière (2016)"
                ),
                "conflict_type": "Direct Human Exposure Conflict",
                "coordinates": {"latitude": 6.101, "longitude": 1.194},
                "buffer_zone_m": 500,
                "affected_road_length_m": 820,
                "key_hazard_indicators": {
                    "estimated_queue_length_m": 820,
                    "estimated_queued_vehicles": 145,
                    "pedestrian_informal_crossing_detected": True,
                    "formal_crossing_infrastructure_detected": False,
                    "vendor_activity_in_roadway_detected": True,
                    "lighting_detected": False,
                    "avg_vehicle_dwell_time_hours_estimated": 8,
                    "emergency_vehicle_access_lane_detected": False,
                },
                "estimated_affected_population": 12000,
                "recommended_action": (
                    "MANDATORY DESIGN INTERVENTION. Border crossing requires "
                    "complete redesign as a safe mixed-use zone. Separate "
                    "pedestrian and vehicle flows physically. Install "
                    "emergency access lane. Full lighting along 820m queue "
                    "zone. Coordinate with both Ghana and Togo border "
                    "authorities under ECOWAS one-stop border post framework."
                ),
                "required_mitigation": [
                    "Pedestrian footbridge or grade-separated crossing over queue zone",
                    "Physical barrier separating pedestrian zone from HGV queue",
                    "Dedicated emergency vehicle access lane (full 820m)",
                    "Full LED lighting coverage — 820m queue zone",
                    "Formal vendor trading zone off carriageway",
                    "CCTV and border safety monitoring system",
                    "Signage in French, English, and Ewe at all approach points",
                    "Coordination with ALCOMA for ECOWAS one-stop border post design",
                ],
                "mitigation_capex_estimated_usd": 7200000,
                "permitting_outlook": (
                    "Requires bilateral agreement between Ghana and Togo under "
                    "ECOWAS framework. ALCOMA is the designated authority for "
                    "border crossing design. Estimated 8–12 month process "
                    "given binational coordination requirement."
                ),
                "dfI_financing_impact": (
                    "Night-time pedestrian exposure to HGVs at border crossings "
                    "is a known fatality risk flagged by AfDB road safety "
                    "guidelines. This conflict will require a standalone "
                    "Road Safety Action Plan as a DFI financing condition."
                ),
                "notes": (
                    "Queue length has grown significantly since 2023 — "
                    "consistent with increased AfCFTA trade volumes. The corridor "
                    "highway project will increase HGV traffic further, making "
                    "this intervention more urgent, not less. Early ALCOMA "
                    "engagement is strongly recommended."
                ),
            },

            # ── HIGH ──────────────────────────────────────────────────────

            {
                "conflict_id": "HSC-004",
                "source_detection": "DET-RS-002",
                "name": "Roadside Market — N1 Highway, Côte d'Ivoire",
                "country": "Cote d'Ivoire",
                "subtype": "Roadside Market — High Pedestrian Density",
                "risk_level": "HIGH",
                "legal_basis": (
                    "World Bank ESS4; Côte d'Ivoire Code de la Route Art. 94; "
                    "WHO Safe Road Design Guidelines"
                ),
                "conflict_type": "Human Exposure — Design Mitigation Required",
                "coordinates": {"latitude": 5.339, "longitude": -3.752},
                "buffer_zone_m": 200,
                "affected_road_length_m": 320,
                "key_hazard_indicators": {
                    "market_stall_structures_detected": 63,
                    "proximity_to_carriageway_m": 8,
                    "vendor_encroachment_on_road_detected": True,
                    "pedestrian_crossing_infrastructure_detected": False,
                    "street_lighting_detected": False,
                    "market_footprint_growth_since_2023_pct": 30,
                },
                "estimated_affected_population": 3200,
                "recommended_action": (
                    "Design dedicated off-road market zone with formal access "
                    "point from highway. Install rumble strips, speed reduction "
                    "signage, and lighting. Vendor relocation incentive programme "
                    "required — enforce through local municipality."
                ),
                "required_mitigation": [
                    "Designated off-road market zone with formal vehicle access",
                    "Rumble strips — 100m approach each direction",
                    "60 km/h speed reduction zone with signage",
                    "LED street lighting — 320m affected section",
                    "Road markings — pedestrian awareness zone",
                    "Vendor relocation incentive programme (coordinate with municipality)",
                ],
                "mitigation_capex_estimated_usd": 650000,
                "permitting_outlook": (
                    "Municipality engagement required for vendor relocation. "
                    "Road works approved through Côte d'Ivoire Ministry of "
                    "Infrastructure. Estimated 3–5 month process."
                ),
                "dfI_financing_impact": (
                    "HIGH risk classification — requires documented mitigation "
                    "plan in ESMP. Not a prior action but must be completed "
                    "before corridor section opens to traffic."
                ),
                "notes": (
                    "Market footprint has grown 30% since 2023 and is actively "
                    "encroaching further toward the carriageway. Early intervention "
                    "is significantly cheaper than post-opening enforcement."
                ),
            },

            {
                "conflict_id": "HSC-005",
                "source_detection": "DET-RS-004",
                "name": "Informal Settlement Encroachment — Tema-Accra Highway",
                "country": "Ghana",
                "subtype": "Informal Settlement — Road Edge Encroachment",
                "risk_level": "HIGH",
                "legal_basis": (
                    "World Bank ESS4; World Bank ESS5 (Land Acquisition & "
                    "Resettlement); Ghana Highway Authority Act (Act 540)"
                ),
                "conflict_type": "Human Exposure — Resettlement & Design Required",
                "coordinates": {"latitude": 5.689, "longitude": 0.071},
                "buffer_zone_m": 200,
                "affected_road_length_m": 510,
                "key_hazard_indicators": {
                    "structure_count_detected": 112,
                    "proximity_to_carriageway_m": 3,
                    "footpath_infrastructure_detected": False,
                    "estimated_population_density": "very_high",
                    "night_lighting_detected": False,
                    "drainage_channel_blocking_road_detected": True,
                    "encroachment_worsened_since_2023": True,
                },
                "estimated_affected_population": 5600,
                "recommended_action": (
                    "Phased approach required: (1) Immediate — install temporary "
                    "barrier and lighting on affected 510m section. "
                    "(2) Medium-term — construct formal footpath with kerb "
                    "separation from carriageway. (3) Long-term — resettlement "
                    "assessment for structures within 5m of carriageway under "
                    "World Bank ESS5. Drainage clearance required immediately."
                ),
                "required_mitigation": [
                    "Temporary safety barrier — immediate installation (510m)",
                    "LED street lighting — 510m section",
                    "Formal footpath with kerb separation — full 510m",
                    "Drainage clearance — channel blocking road shoulder",
                    "Resettlement assessment — structures within 5m of carriageway",
                    "Community engagement plan under World Bank ESS5",
                ],
                "mitigation_capex_estimated_usd": 1800000,
                "permitting_outlook": (
                    "Resettlement triggers World Bank ESS5 — Resettlement Action "
                    "Plan (RAP) required. Ghana Highway Authority and District "
                    "Assembly coordination needed. Estimated 6–9 month process "
                    "for full RAP approval."
                ),
                "dfI_financing_impact": (
                    "ESS5 resettlement trigger is a significant DFI financing "
                    "condition. RAP must be disclosed and approved before "
                    "financial close on affected corridor segments."
                ),
                "notes": (
                    "Settlement encroachment has worsened from 8m to 3m setback "
                    "since 2023. Without intervention, structures will be on the "
                    "carriageway edge by the time the highway opens. "
                    "Early RAP initiation is critical to project timeline."
                ),
            },

            {
                "conflict_id": "HSC-006",
                "source_detection": "DET-RS-008",
                "name": "Sharp Curve — Limited Sight Distance, Cotonou Approach",
                "country": "Benin",
                "subtype": "Sharp Curve — Limited Sight Distance",
                "risk_level": "HIGH",
                "legal_basis": (
                    "World Bank ESS4; Benin Code de la Route (2012); "
                    "AASHTO Green Book Geometric Design Standards"
                ),
                "conflict_type": "Engineering Design Conflict",
                "coordinates": {"latitude": 6.368, "longitude": 2.461},
                "buffer_zone_m": 200,
                "affected_road_length_m": 180,
                "key_hazard_indicators": {
                    "curve_radius_estimated_m": 72,
                    "minimum_safe_radius_at_100kmh_m": 230,
                    "sight_distance_deficit_m": 42,
                    "guardrail_detected": False,
                    "vegetation_obstruction_detected": True,
                    "road_surface_condition": "deteriorated",
                    "opposing_carriageway_visible_from_apex": False,
                },
                "estimated_affected_population": 0,
                "recommended_action": (
                    "Engineering redesign of curve geometry where feasible. "
                    "If realignment not possible: install W-beam guardrail "
                    "full curve length, clear vegetation to restore sight "
                    "distance, resurface carriageway, install chevron warning "
                    "signs and advisory speed of 50 km/h on approach."
                ),
                "required_mitigation": [
                    "Curve geometry realignment assessment (preferred solution)",
                    "W-beam guardrail — full curve length both sides (180m each)",
                    "Vegetation clearance — full sight distance restoration",
                    "Carriageway resurfacing — 180m curve + 100m approach each side",
                    "Chevron alignment markers — full curve",
                    "Advisory speed sign — 50 km/h, 200m advance each direction",
                    "Retroreflective delineators on curve edge",
                ],
                "mitigation_capex_estimated_usd": 920000,
                "permitting_outlook": (
                    "Benin Ministry of Infrastructure approval required for "
                    "realignment. Vegetation clearance may require environmental "
                    "screening. Estimated 2–4 month process."
                ),
                "dfI_financing_impact": (
                    "HIGH classification — must be documented in Road Safety "
                    "Audit and included in ESMP. Mitigation required before "
                    "corridor section opens to full traffic."
                ),
                "notes": (
                    "72m curve radius is significantly below the 230m AASHTO "
                    "minimum for 100 km/h design speed. Deteriorated surface "
                    "and vegetation further compound the risk. "
                    "Road Safety Audit should classify this as a blackspot."
                ),
            },

            {
                "conflict_id": "HSC-007",
                "source_detection": "DET-RS-009",
                "name": "Informal Truck Layby — Lagos-Benin Expressway",
                "country": "Nigeria",
                "subtype": "Truck Layby — Informal Roadside Parking",
                "risk_level": "HIGH",
                "legal_basis": (
                    "World Bank ESS4; Nigeria Federal Highways Act Cap F19; "
                    "Federal Road Safety Corps (FRSC) Regulations"
                ),
                "conflict_type": "Human Exposure — Design Mitigation Required",
                "coordinates": {"latitude": 6.502, "longitude": 3.291},
                "buffer_zone_m": 200,
                "affected_road_length_m": 290,
                "key_hazard_indicators": {
                    "estimated_parked_vehicles": 34,
                    "encroachment_on_carriageway_detected": True,
                    "encroachment_width_estimated_m": 2.4,
                    "proximity_to_bend_m": 95,
                    "lighting_detected": False,
                    "fuel_hawking_activity_detected": True,
                    "truck_maintenance_in_road_detected": True,
                    "occupancy_growth_since_2023_pct": 89,
                },
                "estimated_affected_population": 1800,
                "recommended_action": (
                    "Construct formal truck rest area with adequate capacity "
                    "(minimum 50 bays) at a safe distance from the carriageway. "
                    "Install rumble strips and lighting on existing layby section. "
                    "Coordinate with FRSC for enforcement of no-stopping zone "
                    "on carriageway once formal rest area opens."
                ),
                "required_mitigation": [
                    "Formal truck rest area — minimum 50 bays, off carriageway",
                    "Amenities: fuel, food, toilets, basic maintenance area",
                    "LED lighting — formal rest area and approach roads",
                    "No-stopping zone markings on 290m carriageway section",
                    "Rumble strips — 100m approach each direction",
                    "FRSC enforcement coordination for carriageway clearance",
                ],
                "mitigation_capex_estimated_usd": 3800000,
                "permitting_outlook": (
                    "Nigeria Federal Highways Agency (FHA) land allocation required "
                    "for rest area. FRSC enforcement MOU needed. "
                    "Estimated 5–7 month process."
                ),
                "dfI_financing_impact": (
                    "HIGH classification — rest area provision is a standard "
                    "DFI requirement for long-haul corridor projects. "
                    "Must be included in corridor infrastructure package."
                ),
                "notes": (
                    "Truck occupancy has nearly doubled since 2023. This layby "
                    "is 95m from a bend — a rear-end collision at this location "
                    "with an unlit parked truck would be fatal at highway speed. "
                    "The document's planned 20 service areas should specifically "
                    "address this location."
                ),
            },

            # ── MEDIUM ────────────────────────────────────────────────────

            {
                "conflict_id": "HSC-008",
                "source_detection": "DET-RS-005",
                "name": "Unsignalised Fuel Station — Takoradi Highway",
                "country": "Ghana",
                "subtype": "Fuel Station — Unsignalised Entry/Exit",
                "risk_level": "MEDIUM",
                "legal_basis": (
                    "World Bank ESS4; Ghana Road Safety Authority Guidelines; "
                    "Ghana Highway Authority Standards"
                ),
                "conflict_type": "Design Mitigation Required",
                "coordinates": {"latitude": 4.931, "longitude": -1.762},
                "buffer_zone_m": 100,
                "affected_road_length_m": 120,
                "key_hazard_indicators": {
                    "pump_bays_detected": 8,
                    "deceleration_lane_detected": False,
                    "acceleration_lane_detected": False,
                    "proximity_to_junction_m": 38,
                    "entry_exit_points": 3,
                    "informal_parking_on_carriageway_detected": True,
                },
                "estimated_affected_population": 600,
                "recommended_action": (
                    "Install deceleration and acceleration lanes on both "
                    "entry/exit points. Consolidate 3 access points to 1 "
                    "with proper junction geometry. Rumble strips and "
                    "advance warning signage on approach."
                ),
                "required_mitigation": [
                    "Deceleration lane — minimum 80m taper + 40m full width",
                    "Acceleration lane — minimum 60m taper",
                    "Consolidate access to single point with correct geometry",
                    "Rumble strips — 80m advance each direction",
                    "No-parking markings on adjacent carriageway",
                ],
                "mitigation_capex_estimated_usd": 280000,
                "permitting_outlook": (
                    "Ghana Highway Authority standards compliance. "
                    "Fuel station operator engagement required. "
                    "Estimated 2–3 month process."
                ),
                "dfI_financing_impact": (
                    "MEDIUM classification — included in ESMP but not a "
                    "prior action for financial close."
                ),
                "notes": (
                    "Additional pump bays added in 2025 have increased turning "
                    "movements. Standard access management solution."
                ),
            },

            {
                "conflict_id": "HSC-009",
                "source_detection": "DET-RS-007",
                "name": "Livestock Crossing Zone — Lomé-Cotonou Section",
                "country": "Togo",
                "subtype": "Livestock & Agricultural Crossing Zone",
                "risk_level": "MEDIUM",
                "legal_basis": (
                    "World Bank ESS4; Togo Code de la Route; "
                    "ECOWAS Transhumance Protocols"
                ),
                "conflict_type": "Seasonal Exposure — Design Mitigation Required",
                "coordinates": {"latitude": 6.248, "longitude": 1.612},
                "buffer_zone_m": 100,
                "affected_road_length_m": 240,
                "key_hazard_indicators": {
                    "grazing_land_proximity_m": 18,
                    "formal_livestock_crossing_detected": False,
                    "fencing_along_carriageway_detected": False,
                    "seasonal_peak": "dry_season_migration",
                    "herder_track_crossing_road_detected": True,
                    "warning_signage_detected": False,
                },
                "estimated_affected_population": 400,
                "recommended_action": (
                    "Install livestock fencing along carriageway on both sides "
                    "for 240m section. Create formal livestock underpass or "
                    "at-grade crossing point with cattle grid and warning "
                    "signage. Seasonal warning campaign for drivers."
                ),
                "required_mitigation": [
                    "Livestock fencing — both sides, 240m section",
                    "Formal livestock crossing point with cattle grid",
                    "Advance warning signage — livestock crossing, 300m each direction",
                    "Seasonal speed reduction zone — dry season months",
                    "Community awareness programme with herder associations",
                ],
                "mitigation_capex_estimated_usd": 180000,
                "permitting_outlook": (
                    "Togo Ministry of Agriculture coordination for herder "
                    "engagement. Low permitting complexity. "
                    "Estimated 1–2 month process."
                ),
                "dfI_financing_impact": (
                    "MEDIUM classification — standard livestock management "
                    "measure. Included in ESMP."
                ),
                "notes": (
                    "Seasonal risk aligned to dry-season cattle migration "
                    "patterns. Low-cost intervention with high safety return. "
                    "ECOWAS transhumance protocols provide regional framework "
                    "for herder engagement."
                ),
            },

            # ── LOW ───────────────────────────────────────────────────────

            {
                "conflict_id": "HSC-010",
                "source_detection": "DET-RS-010",
                "name": "Active Road Works — Lagos Ring Road",
                "country": "Nigeria",
                "subtype": "Road Works — Active Construction Zone",
                "risk_level": "LOW",
                "legal_basis": (
                    "World Bank ESS4; Nigeria Highway Safety Regulations; "
                    "FRSC Temporary Traffic Management Guidelines"
                ),
                "conflict_type": "Temporary Exposure — Standard Management Required",
                "coordinates": {"latitude": 6.548, "longitude": 3.328},
                "buffer_zone_m": 100,
                "affected_road_length_m": 3100,
                "key_hazard_indicators": {
                    "lane_reduction_detected": True,
                    "lanes_reduced_from": 3,
                    "lanes_reduced_to": 1,
                    "temporary_signage_detected": False,
                    "construction_equipment_count": 11,
                    "traffic_marshal_positions_detected": False,
                    "night_lighting_on_works_detected": False,
                },
                "estimated_affected_population": 22000,
                "recommended_action": (
                    "Immediately deploy Temporary Traffic Management (TTM) "
                    "plan: advance warning signs, traffic marshals at "
                    "contraflow points, night lighting on active works, "
                    "and speed limit of 30 km/h through works zone. "
                    "Standard construction site safety requirement."
                ),
                "required_mitigation": [
                    "Temporary traffic management plan — deploy immediately",
                    "Advance warning signs — 500m each direction",
                    "Traffic marshals — contraflow entry/exit points",
                    "Night lighting — full 3.1 km works zone",
                    "30 km/h speed limit with cones and signage",
                    "Daily site safety briefings for construction crews",
                ],
                "mitigation_capex_estimated_usd": 45000,
                "permitting_outlook": (
                    "FRSC notification required for road works. "
                    "Standard process — estimated 2 weeks."
                ),
                "dfI_financing_impact": (
                    "LOW classification — standard construction site safety. "
                    "Monitored through contractor ESMP compliance."
                ),
                "notes": (
                    "Works commenced Q3 2025. Three-lane to one-lane reduction "
                    "over 3.1 km with no signage or marshals is a significant "
                    "near-term risk. Immediate TTM deployment required."
                ),
            },
        ],

        # ================================================================
        # NO-GO ZONES (environmental + human safety combined)
        # ================================================================

        "no_go_zones": [

            # — Environmental No-Go Zones (original) —
            {
                "zone_id": "NGZ-001",
                "category": "environmental",
                "name": "Ankasa Conservation Area — Core Zone",
                "coordinates": {"latitude": 5.271, "longitude": -2.694},
                "radius_km": 15.2,
                "classification": "ABSOLUTE NO-GO",
                "reason": (
                    "IUCN Category II + IFC PS6 Critical Habitat — "
                    "no permits will be granted"
                ),
            },
            {
                "zone_id": "NGZ-002",
                "category": "environmental",
                "name": "Keta Lagoon Ramsar Site",
                "coordinates": {"latitude": 5.920, "longitude": 0.980},
                "radius_km": 6.8,
                "classification": "ABSOLUTE NO-GO",
                "reason": (
                    "Ramsar Convention international treaty obligation — "
                    "infrastructure prohibited within boundary"
                ),
            },
            {
                "zone_id": "NGZ-003",
                "category": "environmental",
                "name": "Omo Forest Reserve — Core Zone",
                "coordinates": {"latitude": 6.718, "longitude": 4.352},
                "radius_km": 11.0,
                "classification": "HARD NO-GO",
                "reason": (
                    "Nigeria Forestry Act + AfDB Category 1 trigger — "
                    "permit denied in practice"
                ),
            },

            # — Human Safety No-Go Zones (new) —
            {
                "zone_id": "NGZ-RS-001",
                "category": "human_safety",
                "source_conflict": "HSC-002",
                "source_detection": "DET-RS-003",
                "name": "Primary School Safety Exclusion Zone — Tema",
                "coordinates": {"latitude": 5.671, "longitude": -0.002},
                "radius_km": 0.2,
                "classification": "DESIGN INTERVENTION REQUIRED",
                "reason": (
                    "CRITICAL — school 6m from carriageway, 400 children at risk. "
                    "ESS4 mandatory prior action. No construction on this segment "
                    "until pedestrian crossing and speed mitigation installed."
                ),
            },
            {
                "zone_id": "NGZ-RS-002",
                "category": "human_safety",
                "source_conflict": "HSC-003",
                "source_detection": "DET-RS-006",
                "name": "Ghana-Togo Border Crossing Safety Zone",
                "coordinates": {"latitude": 6.101, "longitude": 1.194},
                "radius_km": 0.5,
                "classification": "DESIGN INTERVENTION REQUIRED",
                "reason": (
                    "CRITICAL — 820m pedestrian-HGV conflict zone, no lighting. "
                    "ESS4 mandatory prior action. Border redesign required "
                    "before corridor traffic volumes increase."
                ),
            },
            {
                "zone_id": "NGZ-RS-003",
                "category": "human_safety",
                "source_conflict": "HSC-001",
                "source_detection": "DET-RS-001",
                "name": "Uncontrolled Junction Safety Zone — Abidjan Port Approach",
                "coordinates": {"latitude": 5.312, "longitude": -3.994},
                "radius_km": 0.2,
                "classification": "DESIGN INTERVENTION REQUIRED",
                "reason": (
                    "CRITICAL — 5-arm uncontrolled junction, no signals, "
                    "vendor encroachment. ESS4 mandatory prior action. "
                    "Junction redesign must be completed before construction begins."
                ),
            },
        ],

        # ================================================================
        # AGGREGATE IMPACT (updated to include safety)
        # ================================================================

        "aggregate_impact": {

            # — Environmental (original) —
            "total_protected_area_conflicts": 4,
            "total_wetland_conflicts": 2,
            "total_cultural_heritage_conflicts": 1,
            "total_rerouting_required_km": 31,
            "total_rerouting_capex_usd": 21000000,
            "total_underground_cable_required_km": 3.8,
            "pct_corridor_environmentally_constrained": 8.4,

            # — Human Safety (new) —
            "total_human_safety_conflicts": 10,
            "human_safety_conflicts_by_severity": {
                "CRITICAL": 3,
                "HIGH": 4,
                "MEDIUM": 2,
                "LOW": 1,
            },
            "total_human_safety_mitigation_capex_usd": 19225000,
            "human_safety_capex_breakdown": {
                "HSC-001_junction_redesign": 3500000,
                "HSC-002_school_zone": 850000,
                "HSC-003_border_crossing": 7200000,
                "HSC-004_market_zone": 650000,
                "HSC-005_settlement_resettlement": 1800000,
                "HSC-006_sharp_curve": 920000,
                "HSC-007_truck_layby": 3800000,
                "HSC-008_fuel_station": 280000,
                "HSC-009_livestock_crossing": 180000,
                "HSC-010_road_works_ttm": 45000,
            },
            "total_estimated_population_in_conflict_zones": 54400,
            "pct_corridor_with_human_safety_conflicts": 4.2,

            # — Combined —
            "total_all_conflicts": 17,
            "total_combined_mitigation_capex_usd": 40225000,
            "esg_risk_rating_for_dfi_financing": "Moderate-High — manageable with mitigation",

            "estimated_permitting_duration_months": {
                "environmental_best_case": 14,
                "environmental_base_case": 20,
                "environmental_worst_case": 30,
                "human_safety_prior_actions_required_before_financial_close": 3,
                "human_safety_prior_actions_estimated_months": 6,
            },

            "dfI_financing_risk": (
                "Moderate — environmental conflicts are resolvable through re-routing. "
                "3 CRITICAL human safety conflicts (HSC-001, HSC-002, HSC-003) are "
                "ESS4 prior actions that must be resolved before financial close. "
                "No conflict currently disqualifies DFI financing if all recommended "
                "mitigations are adopted and the Road Safety Action Plan is approved."
            ),
        },

        # ================================================================
        # RECOMMENDED NEXT STEPS (updated to include safety actions)
        # ================================================================

        "recommended_next_steps": [

            # — Environmental (original) —
            "Adopt all 3 hard re-routes (ENV-001, ENV-002, ENV-003) in route design before engineering progresses — re-routing post-design adds 6–9 months",
            "Initiate Ramsar notification (WET-001) immediately — international treaty process has fixed timelines independent of project schedule",
            "Commission Phase 1 Environmental and Social Assessment (ESIA scoping) — required by all DFI lenders before financial close",
            "Begin early engagement with Ghana Forestry Commission (ENV-002) and VRA (WET-002) — both have long institutional consultation requirements",
            "Submit re-routed alignment to route optimization agent as updated constraint layer",

            # — Human Safety (new) —
            "IMMEDIATE: Issue construction halt notice on road-facing classroom block at Tema school (HSC-002) — setback will become non-compliant when completed",
            "IMMEDIATE: Deploy Temporary Traffic Management plan at Lagos road works (HSC-010) — no signage or marshals currently present",
            "Commission standalone Road Safety Action Plan (RSAP) — required by AfDB and World Bank as financing condition for road projects",
            "Initiate bilateral ALCOMA engagement for Ghana-Togo border crossing redesign (HSC-003) — binational process has longest lead time of all safety mitigations",
            "Instruct design team to include junction redesign (HSC-001), school zone (HSC-002), and border crossing (HSC-003) as Phase 1 prior actions in financing term sheet",
            "Commission independent Road Safety Audit of full 1,080 km corridor — identify additional blackspots beyond satellite-detected hazards",
            "Engage Ghana NRSA, Togo Road Safety Authority, Nigeria FRSC, and Côte d'Ivoire OSER as national road safety authority partners for corridor-wide safety programme",
            "Submit human safety no-go zones (NGZ-RS-001, NGZ-RS-002, NGZ-RS-003) to route optimization agent alongside environmental no-go zones",
        ],

        # ================================================================
        # OUTPUT URIS (updated to include safety outputs)
        # ================================================================

        "output_uris": {
            # — Environmental (original) —
            "constraints_geojson": (
                "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                "environmental/constraints_layer.geojson"
            ),
            "no_go_zones_geojson": (
                "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                "environmental/no_go_zones.geojson"
            ),
            "conflict_report_pdf": (
                "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                "environmental/environmental_audit_report.pdf"
            ),
            "esia_scope_checklist": (
                "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                "environmental/esia_scoping_checklist.json"
            ),
            # — Human Safety (new) —
            "human_safety_conflicts_geojson": (
                "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                "safety/human_safety_conflicts.geojson"
            ),
            "safety_no_go_zones_geojson": (
                "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                "safety/safety_no_go_zones.geojson"
            ),
            "road_safety_action_plan_template": (
                "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                "safety/rsap_template.json"
            ),
            "esmp_safety_chapter": (
                "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                "safety/esmp_safety_chapter.pdf"
            ),
            "combined_no_go_zones_geojson": (
                "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                "combined/all_no_go_zones_environmental_and_safety.geojson"
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