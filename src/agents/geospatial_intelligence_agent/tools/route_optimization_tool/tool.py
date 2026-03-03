import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import RouteOptimizationInput


@tool("route_optimization", description=TOOL_DESCRIPTION)
def route_optimization_tool(
    payload: RouteOptimizationInput, runtime: ToolRuntime
) -> Command:
    """
    Calculates the most efficient infrastructure paths by combining
    terrain, environmental, human safety, and infrastructure data.

    Priority modes:
    - "min_cost"    : Minimise total net CAPEX
    - "min_distance": Minimise total route length
    - "max_impact"  : Maximise anchor load coverage and economic impact
    - "balance"     : Balanced optimisation across all dimensions (default)
    - "max_safety"  : Weight road_safety_score highest — actively routes
                      around CRITICAL and HIGH human safety conflict zones
                      even at additional CAPEX. Satisfies DFI ESS4 prior
                      action requirements as primary objective.

    Road Safety Integration:
    - Human safety conflicts (HSC-001 to HSC-010) from environmental_constraints
      tool are consumed as hard and soft constraints alongside environmental NGZs.
    - CRITICAL safety zones (NGZ-RS-001 to NGZ-RS-003) are treated as hard
      constraints equivalent to environmental no-go zones.
    - HIGH/MEDIUM safety zones apply penalty costs to the weighted cost grid.
    - road_safety_score is added to scoring_breakdown for all route variants.
    - safety_capex_usd is added to segment and route totals.
    - safety_interventions_required is added to phasing_recommendation phases.

    In a real-world scenario, this tool would:
    1. Create a Weighted Cost Grid where:
       - Environmental NGZ pixels = Infinite Cost (hard constraint)
       - Human Safety NGZ pixels = Infinite Cost (hard constraint, NEW)
       - CRITICAL safety zone pixels = Very High Cost (soft — avoidance preferred)
       - HIGH safety zone pixels = High Cost (soft — reroute if low overhead)
       - MEDIUM/LOW safety zone pixels = Moderate Cost (design mitigation added)
    2. Use A* or Dijkstra's algorithm to find lowest-accumulated-cost path.
    3. Smooth the line to meet engineering turning radius standards.
    4. Calculate co-location % by checking proximity to transport layers.
    5. For each route segment passing through a safety conflict zone,
       add the mitigation CAPEX from HSC conflict records to segment cost.
    """

    response = {
        "job_metadata": {
            "tool": "route_optimization",
            "corridor_id": "ABIDJAN_LAGOS_CORRIDOR",
            "algorithm": "Multi-Criteria Least-Cost Path (A* on Weighted Cost Grid)",
            "priority_mode": "balance",
            "inputs_consumed": {
                # — Original inputs —
                "dem_raster": (
                    "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                    "dem/srtm_gl1_void_filled_30m.tif"
                ),
                "land_use_raster": (
                    "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                    "land_use/esa_worldcover_2021_10m.tif"
                ),
                "no_go_zones_geojson": (
                    "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                    "environmental/no_go_zones.geojson"
                ),
                "constraints_geojson": (
                    "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                    "environmental/constraints_layer.geojson"
                ),
                "osm_infrastructure_uri": (
                    "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                    "vectors/osm_infrastructure_extract.geojson"
                ),
                "detections_geojson": (
                    "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                    "detections/infrastructure_detections.geojson"
                ),
                # — New road safety inputs —
                "combined_no_go_zones_geojson": (
                    "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                    "combined/all_no_go_zones_environmental_and_safety.geojson"
                ),
                "human_safety_conflicts_geojson": (
                    "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                    "safety/human_safety_conflicts.geojson"
                ),
                "road_safety_hazards_geojson": (
                    "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                    "detections/road_safety_hazards.geojson"
                ),
                "road_safety_heatmap_raster": (
                    "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                    "detections/road_safety_heatmap.tif"
                ),
                "night_lights_raster": (
                    "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                    "rasters/viirs_night_lights_2025.tif"
                ),
                "population_density_raster": (
                    "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                    "rasters/worldpop_2025_100m.tif"
                ),
            },
            "cost_grid_resolution_m": 30,
            "cost_grid_dimensions": {"rows": 14820, "cols": 38640},
            "variants_requested": 75,
            "variants_generated": 75,
            "variants_passing_hard_constraints": 58,
            "variants_passing_hard_constraints_note": (
                "3 additional variants eliminated vs. original run due to "
                "NGZ-RS-001 (Tema school), NGZ-RS-002 (Ghana-Togo border), "
                "and NGZ-RS-003 (Abidjan junction) hard safety constraints."
            ),
            "top_n_returned": 5,
            "processing_time_seconds": 912,
            "generated_at": "2026-01-26T09:41:03+00:00",
        },
        # ================================================================
        # COST WEIGHT MATRIX
        # Updated to include road_safety_score as a scored dimension.
        # Weights rebalanced: highway_corridor_proximity reduced from 0.20
        # to 0.15 to accommodate road_safety_sensitivity at 0.10.
        # Sum still = 1.0.
        # ================================================================
        "cost_weight_matrix": {
            "description": (
                "Weights applied to each factor in the cost grid. Sum = 1.0. "
                "Road safety sensitivity added as explicit scoring dimension. "
                "CRITICAL safety NGZs treated as infinite-cost hard constraints "
                "equivalent to environmental no-go zones."
            ),
            "terrain_slope": 0.25,
            "land_acquisition_cost": 0.20,
            "environmental_sensitivity": 0.20,
            "construction_logistics": 0.15,
            "highway_corridor_proximity": 0.10,
            "road_safety_sensitivity": 0.10,
            "no_go_zone_penalty": "Infinite (hard constraint — environmental AND safety NGZs)",
            "safety_zone_penalties": {
                "CRITICAL_human_safety_zone": (
                    "Very High — strong avoidance preference. "
                    "If unavoidable, mandatory mitigation CAPEX added."
                ),
                "HIGH_human_safety_zone": (
                    "High — reroute preferred if overhead < 5% additional length. "
                    "Otherwise mitigation CAPEX added to segment cost."
                ),
                "MEDIUM_human_safety_zone": (
                    "Moderate — standard design mitigation CAPEX added. "
                    "No rerouting required."
                ),
                "LOW_human_safety_zone": (
                    "Minor — TTM/signage CAPEX added. Minimal route influence."
                ),
            },
        },
        # ================================================================
        # ROAD SAFETY CONFLICT REGISTER
        # Summarises all HSC conflicts consumed from environmental_constraints
        # tool and how each is treated in the cost grid and CAPEX estimates.
        # ================================================================
        "road_safety_conflict_register": {
            "total_conflicts_consumed": 10,
            "hard_constraint_zones": [
                {
                    "ngz_id": "NGZ-RS-001",
                    "source_conflict": "HSC-002",
                    "source_detection": "DET-RS-003",
                    "name": "Primary School Safety Zone — Tema",
                    "treatment": "INFINITE COST — hard constraint",
                    "impact_on_routing": (
                        "All variants passing within 200m of school without "
                        "confirmed pedestrian crossing design are eliminated. "
                        "3 variants eliminated in this run."
                    ),
                    "mandatory_prior_action": True,
                    "mitigation_capex_usd": 850000,
                },
                {
                    "ngz_id": "NGZ-RS-002",
                    "source_conflict": "HSC-003",
                    "source_detection": "DET-RS-006",
                    "name": "Ghana-Togo Border Crossing Safety Zone",
                    "treatment": "INFINITE COST — hard constraint",
                    "impact_on_routing": (
                        "Corridor design through border zone requires confirmed "
                        "pedestrian separation design. Variants without border "
                        "redesign commitment are eliminated."
                    ),
                    "mandatory_prior_action": True,
                    "mitigation_capex_usd": 7200000,
                },
                {
                    "ngz_id": "NGZ-RS-003",
                    "source_conflict": "HSC-001",
                    "source_detection": "DET-RS-001",
                    "name": "Uncontrolled Junction Safety Zone — Abidjan Port",
                    "treatment": "INFINITE COST — hard constraint",
                    "impact_on_routing": (
                        "Port approach route variants require junction redesign "
                        "commitment. Variants bypassing junction entirely are "
                        "preferred and score higher on road_safety_score."
                    ),
                    "mandatory_prior_action": True,
                    "mitigation_capex_usd": 3500000,
                },
            ],
            "soft_constraint_zones": [
                {
                    "hsc_id": "HSC-004",
                    "source_detection": "DET-RS-002",
                    "name": "Roadside Market — N1 Highway, Côte d'Ivoire",
                    "severity": "HIGH",
                    "treatment": "High penalty cost — reroute if low overhead",
                    "mitigation_capex_usd": 650000,
                },
                {
                    "hsc_id": "HSC-005",
                    "source_detection": "DET-RS-004",
                    "name": "Informal Settlement — Tema-Accra Highway",
                    "severity": "HIGH",
                    "treatment": "High penalty cost — reroute if low overhead",
                    "mitigation_capex_usd": 1800000,
                },
                {
                    "hsc_id": "HSC-006",
                    "source_detection": "DET-RS-008",
                    "name": "Sharp Curve — Cotonou Approach",
                    "severity": "HIGH",
                    "treatment": "High penalty cost — engineering redesign preferred",
                    "mitigation_capex_usd": 920000,
                },
                {
                    "hsc_id": "HSC-007",
                    "source_detection": "DET-RS-009",
                    "name": "Informal Truck Layby — Lagos-Benin Expressway",
                    "severity": "HIGH",
                    "treatment": "High penalty cost — formal rest area required",
                    "mitigation_capex_usd": 3800000,
                },
                {
                    "hsc_id": "HSC-008",
                    "source_detection": "DET-RS-005",
                    "name": "Fuel Station — Takoradi Highway",
                    "severity": "MEDIUM",
                    "treatment": "Moderate penalty — access lane mitigation added",
                    "mitigation_capex_usd": 280000,
                },
                {
                    "hsc_id": "HSC-009",
                    "source_detection": "DET-RS-007",
                    "name": "Livestock Crossing — Lomé-Cotonou",
                    "severity": "MEDIUM",
                    "treatment": "Moderate penalty — fencing and crossing mitigation",
                    "mitigation_capex_usd": 180000,
                },
                {
                    "hsc_id": "HSC-010",
                    "source_detection": "DET-RS-010",
                    "name": "Road Works — Lagos Ring Road",
                    "severity": "LOW",
                    "treatment": "Minor penalty — TTM plan CAPEX added",
                    "mitigation_capex_usd": 45000,
                },
            ],
            "total_safety_mitigation_capex_all_conflicts_usd": 19225000,
        },
        # ================================================================
        # OPTIMISED ROUTES (all 5 variants)
        # Changes per variant:
        # - road_safety_score added to scoring_breakdown
        # - safety_conflicts_mitigated added to each variant
        # - safety_capex_usd added to totals
        # - combined_net_capex_including_safety_usd added to totals
        # - Per-segment: safety_conflicts_on_segment + safety_capex_usd
        # ================================================================
        "optimized_routes": [
            {
                "variant_id": "ROUTE-V1",
                "rank": 1,
                "label": "Recommended — Coastal Highway Co-location",
                "description": (
                    "Follows N1/A1 coastal highway alignment for 71% of route. "
                    "Applies all environmental re-routes and all mandatory "
                    "safety mitigations. Balances CAPEX and construction risk. "
                    "Achieves highest composite score including road safety dimension."
                ),
                "total_length_km": 1094.2,
                "vs_straight_line_overhead_pct": 1.3,
                "composite_score": 87.4,
                "coordinates": [
                    [5.350, -4.020],
                    [5.182, -3.800],
                    [5.110, -3.200],
                    [5.050, -2.788],
                    [5.100, -2.200],
                    [5.200, -1.600],
                    [5.350, -1.100],
                    [5.500, -0.500],
                    [5.620, -0.200],
                    [5.666, -0.044],
                    [5.900, 0.300],
                    [6.032, 0.607],
                    [6.150, 0.900],
                    [6.200, 1.100],
                    [6.137, 1.222],
                    [6.250, 1.600],
                    [6.350, 2.000],
                    [6.365, 2.406],
                    [6.420, 2.700],
                    [6.440, 3.000],
                    [6.400, 3.400],
                    [6.438, 3.700],
                    [6.450, 3.870],
                    [6.438, 3.989],
                    [6.427, 3.987],
                    [6.563, 3.564],
                ],
                "route_geojson": {
                    "type": "LineString",
                    "coordinates": [
                        [-4.020, 5.350],
                        [-3.800, 5.182],
                        [-3.200, 5.110],
                        [-2.788, 5.050],
                        [-2.200, 5.100],
                        [-1.600, 5.200],
                        [-1.100, 5.350],
                        [-0.500, 5.500],
                        [-0.200, 5.620],
                        [-0.044, 5.666],
                        [0.300, 5.900],
                        [0.607, 6.032],
                        [0.900, 6.150],
                        [1.100, 6.200],
                        [1.222, 6.137],
                        [1.600, 6.250],
                        [2.000, 6.350],
                        [2.406, 6.365],
                        [2.700, 6.420],
                        [3.000, 6.440],
                        [3.400, 6.400],
                        [3.700, 6.438],
                        [3.870, 6.450],
                        [3.989, 6.438],
                        [3.987, 6.427],
                        [3.564, 6.563],
                    ],
                },
                "scoring_breakdown": {
                    "capex_score": 82,
                    "terrain_score": 91,
                    "environmental_score": 95,
                    "co_location_score": 88,
                    "anchor_load_coverage": 84,
                    # — NEW —
                    "road_safety_score": 86,
                    "road_safety_score_rationale": (
                        "All 3 CRITICAL safety NGZs mitigated by design commitment. "
                        "4 HIGH conflicts addressed through co-location reroute or "
                        "mitigation CAPEX. 3 MEDIUM/LOW conflicts have standard "
                        "design measures applied. Score reflects full compliance "
                        "with ESS4 prior actions."
                    ),
                },
                # — NEW: safety conflicts mitigated on this variant —
                "safety_conflicts_mitigated": {
                    "critical_prior_actions": [
                        {
                            "conflict_id": "HSC-001",
                            "name": "Abidjan Junction Redesign",
                            "treatment_applied": (
                                "Route avoids direct junction overlap. "
                                "Signalised roundabout design committed in "
                                "corridor master plan. CAPEX added to SEG-001."
                            ),
                            "mitigation_capex_usd": 3500000,
                        },
                        {
                            "conflict_id": "HSC-002",
                            "name": "Tema School Zone",
                            "treatment_applied": (
                                "Pedestrian crossing + speed table + fencing "
                                "committed as Phase 1 prior action. Construction "
                                "halt on road-facing classroom block confirmed. "
                                "CAPEX added to SEG-001."
                            ),
                            "mitigation_capex_usd": 850000,
                        },
                        {
                            "conflict_id": "HSC-003",
                            "name": "Ghana-Togo Border Crossing Redesign",
                            "treatment_applied": (
                                "Pedestrian footbridge + physical barrier + "
                                "full lighting committed. ALCOMA bilateral "
                                "engagement initiated. CAPEX added to SEG-002."
                            ),
                            "mitigation_capex_usd": 7200000,
                        },
                    ],
                    "high_conflicts": [
                        {
                            "conflict_id": "HSC-004",
                            "treatment_applied": "Designated off-road market zone + rumble strips + lighting. CAPEX added to SEG-001.",
                            "mitigation_capex_usd": 650000,
                        },
                        {
                            "conflict_id": "HSC-005",
                            "treatment_applied": "Formal footpath + kerb separation + drainage clearance + RAP initiated. CAPEX added to SEG-001.",
                            "mitigation_capex_usd": 1800000,
                        },
                        {
                            "conflict_id": "HSC-006",
                            "treatment_applied": "W-beam guardrail + vegetation clearance + resurfacing + chevron markers. CAPEX added to SEG-003.",
                            "mitigation_capex_usd": 920000,
                        },
                        {
                            "conflict_id": "HSC-007",
                            "treatment_applied": "Formal truck rest area (50 bays) + lighting + FRSC enforcement MOU. CAPEX added to SEG-004.",
                            "mitigation_capex_usd": 3800000,
                        },
                    ],
                    "medium_low_conflicts": [
                        {
                            "conflict_id": "HSC-008",
                            "treatment_applied": "Deceleration/acceleration lanes + access consolidation. CAPEX added to SEG-001.",
                            "mitigation_capex_usd": 280000,
                        },
                        {
                            "conflict_id": "HSC-009",
                            "treatment_applied": "Livestock fencing + formal crossing + seasonal signage. CAPEX added to SEG-003.",
                            "mitigation_capex_usd": 180000,
                        },
                        {
                            "conflict_id": "HSC-010",
                            "treatment_applied": "TTM plan deployed immediately + night lighting on works. CAPEX added to SEG-004.",
                            "mitigation_capex_usd": 45000,
                        },
                    ],
                    "total_safety_mitigation_capex_this_route_usd": 19225000,
                },
                "segments": [
                    {
                        "segment_id": "V1-SEG-001",
                        "label": "Abidjan → Tema",
                        "country_span": ["Côte d'Ivoire", "Ghana (West)"],
                        "length_km": 322,
                        "voltage_kv": 400,
                        "capacity_mw": 800,
                        "highway_overlap_pct": 78,
                        "capex_usd": 415000000,
                        "co_location_saving_usd": 70550000,
                        "net_capex_usd": 344450000,
                        "terrain_difficulty": "Easy",
                        "environmental_conflicts_resolved": [
                            "ENV-002 (Nzema Forest — northern detour applied)",
                        ],
                        # — NEW —
                        "safety_conflicts_on_segment": [
                            "HSC-001 (Abidjan Junction — CRITICAL prior action)",
                            "HSC-002 (Tema School Zone — CRITICAL prior action)",
                            "HSC-004 (N1 Roadside Market — HIGH)",
                            "HSC-005 (Tema-Accra Settlement — HIGH)",
                            "HSC-008 (Takoradi Fuel Station — MEDIUM)",
                        ],
                        "safety_capex_usd": 7080000,
                        "net_capex_including_safety_usd": 351530000,
                        "road_safety_segment_rating": "COMPLIANT — all conflicts mitigated",
                        "key_anchor_loads_served": [
                            "DET-001 (Azito)",
                            "DET-002 (CIPREL)",
                            "DET-005 (Port of Abidjan)",
                        ],
                        "coordinates": [
                            [5.350, -4.020],
                            [5.182, -3.800],
                            [5.110, -3.200],
                            [5.050, -2.788],
                            [5.100, -2.200],
                            [5.200, -1.600],
                            [5.350, -1.100],
                            [5.500, -0.500],
                            [5.620, -0.200],
                            [5.666, -0.044],
                        ],
                        "route_geojson": {
                            "type": "LineString",
                            "coordinates": [
                                [-4.020, 5.350],
                                [-3.800, 5.182],
                                [-3.200, 5.110],
                                [-2.788, 5.050],
                                [-2.200, 5.100],
                                [-1.600, 5.200],
                                [-1.100, 5.350],
                                [-0.500, 5.500],
                                [-0.200, 5.620],
                                [-0.044, 5.666],
                            ],
                        },
                    },
                    {
                        "segment_id": "V1-SEG-002",
                        "label": "Tema → Lomé",
                        "country_span": ["Ghana (East)", "Togo"],
                        "length_km": 188,
                        "voltage_kv": 330,
                        "capacity_mw": 500,
                        "highway_overlap_pct": 44,
                        "capex_usd": 226000000,
                        "co_location_saving_usd": 19710000,
                        "net_capex_usd": 206290000,
                        "terrain_difficulty": "Very Difficult",
                        "environmental_conflicts_resolved": [
                            "ENV-001 (Ankasa — 14km northern detour applied)",
                            "WET-001 (Keta Lagoon — northern re-route + pile foundations)",
                        ],
                        "special_construction": (
                            "Pile-supported towers across 22 km Volta delta; "
                            "420m Pra River span bridge"
                        ),
                        # — NEW —
                        "safety_conflicts_on_segment": [
                            "HSC-003 (Ghana-Togo Border Crossing — CRITICAL prior action)",
                        ],
                        "safety_capex_usd": 7200000,
                        "net_capex_including_safety_usd": 213490000,
                        "road_safety_segment_rating": "COMPLIANT — CRITICAL prior action mitigated",
                        "key_anchor_loads_served": [
                            "Tema Free Zone",
                            "Tema Oil Refinery",
                            "Akosombo Dam interconnection",
                        ],
                        "coordinates": [
                            [5.666, -0.044],
                            [5.900, 0.300],
                            [6.032, 0.607],
                            [6.150, 0.900],
                            [6.200, 1.100],
                            [6.137, 1.222],
                        ],
                        "route_geojson": {
                            "type": "LineString",
                            "coordinates": [
                                [-0.044, 5.666],
                                [0.300, 5.900],
                                [0.607, 6.032],
                                [0.900, 6.150],
                                [1.100, 6.200],
                                [1.222, 6.137],
                            ],
                        },
                    },
                    {
                        "segment_id": "V1-SEG-003",
                        "label": "Lomé → Cotonou",
                        "country_span": ["Togo", "Benin"],
                        "length_km": 158,
                        "voltage_kv": 330,
                        "capacity_mw": 500,
                        "highway_overlap_pct": 81,
                        "capex_usd": 174000000,
                        "co_location_saving_usd": 27840000,
                        "net_capex_usd": 146160000,
                        "terrain_difficulty": "Easy-Moderate",
                        "environmental_conflicts_resolved": [
                            "WET-002 (Mono River — elevated crossing + VRA-style permit)",
                        ],
                        # — NEW —
                        "safety_conflicts_on_segment": [
                            "HSC-006 (Cotonou Sharp Curve — HIGH)",
                            "HSC-009 (Livestock Crossing Lomé-Cotonou — MEDIUM)",
                        ],
                        "safety_capex_usd": 1100000,
                        "net_capex_including_safety_usd": 147260000,
                        "road_safety_segment_rating": "COMPLIANT — all conflicts mitigated",
                        "key_anchor_loads_served": [
                            "Port of Lomé",
                            "Port of Cotonou",
                            "Zone Industrielle Cotonou",
                            "TEC Maria Gleta Plant",
                        ],
                        "coordinates": [
                            [6.137, 1.222],
                            [6.250, 1.600],
                            [6.350, 2.000],
                            [6.365, 2.406],
                        ],
                        "route_geojson": {
                            "type": "LineString",
                            "coordinates": [
                                [1.222, 6.137],
                                [1.600, 6.250],
                                [2.000, 6.350],
                                [2.406, 6.365],
                            ],
                        },
                    },
                    {
                        "segment_id": "V1-SEG-004",
                        "label": "Cotonou → Lagos",
                        "country_span": ["Benin", "Nigeria"],
                        "length_km": 426,
                        "voltage_kv": 400,
                        "capacity_mw": 800,
                        "highway_overlap_pct": 62,
                        "capex_usd": 534000000,
                        "co_location_saving_usd": 64080000,
                        "net_capex_usd": 469920000,
                        "terrain_difficulty": "Difficult",
                        "environmental_conflicts_resolved": [
                            "ENV-003 (Omo Forest — 6km southern detour)",
                            "ENV-004 (Lekki — 3.8km underground cable section)",
                        ],
                        "special_construction": (
                            "38 km underground XLPE cable through Lagos urban core; "
                            "Lagos Lagoon submarine crossing (7.2 km)"
                        ),
                        # — NEW —
                        "safety_conflicts_on_segment": [
                            "HSC-007 (Lagos Truck Layby — HIGH)",
                            "HSC-010 (Lagos Road Works — LOW)",
                        ],
                        "safety_capex_usd": 3845000,
                        "net_capex_including_safety_usd": 473765000,
                        "road_safety_segment_rating": "COMPLIANT — all conflicts mitigated",
                        "key_anchor_loads_served": [
                            "DET-003 (Dangote Refinery)",
                            "DET-004 (Lekki FTZ)",
                            "Egbin Power Station",
                            "MainOne Data Center",
                        ],
                        "coordinates": [
                            [6.365, 2.406],
                            [6.420, 2.700],
                            [6.440, 3.000],
                            [6.400, 3.400],
                            [6.438, 3.700],
                            [6.450, 3.870],
                            [6.438, 3.989],
                            [6.427, 3.987],
                            [6.563, 3.564],
                        ],
                        "route_geojson": {
                            "type": "LineString",
                            "coordinates": [
                                [2.406, 6.365],
                                [2.700, 6.420],
                                [3.000, 6.440],
                                [3.400, 6.400],
                                [3.700, 6.438],
                                [3.870, 6.450],
                                [3.989, 6.438],
                                [3.987, 6.427],
                                [3.564, 6.563],
                            ],
                        },
                    },
                ],
                "totals": {
                    "gross_capex_usd": 1349000000,
                    "total_co_location_saving_usd": 182180000,
                    "co_location_saving_pct": 13.5,
                    "net_capex_usd": 1166820000,
                    # — NEW —
                    "total_safety_mitigation_capex_usd": 19225000,
                    "combined_net_capex_including_safety_usd": 1186045000,
                    "safety_capex_as_pct_of_net_capex": 1.6,
                    "total_length_km": 1094.2,
                    "weighted_avg_highway_overlap_pct": 67,
                    "anchor_loads_within_15km": 47,
                    "anchor_loads_directly_served": 31,
                    "safety_conflicts_fully_mitigated": 10,
                    "safety_conflicts_partially_mitigated": 0,
                    "ess4_prior_actions_addressed": 3,
                    "esg_compliance_rating": "FULL — all ESS4 prior actions resolved",
                },
                "financial_indicators": {
                    "estimated_year5_throughput_gwh": 4800,
                    "estimated_year5_revenue_usd": 96000000,
                    "estimated_year5_ebitda_usd": 72000000,
                    "indicative_equity_irr_pct": 14.2,
                    "indicative_project_irr_pct": 10.1,
                    "indicative_payback_years": 12,
                    # — NEW —
                    "safety_capex_irr_impact_note": (
                        "Safety CAPEX of $19.2M represents 1.6% addition to net CAPEX. "
                        "IRR impact: -0.2% (14.2% → 14.0% on safety-adjusted basis). "
                        "Offset by: (a) DFI financing cost reduction from ESS4 compliance "
                        "(est. -0.3% WACC improvement = +$18M NPV); (b) reduced construction "
                        "delay risk from pre-resolved prior actions (est. +$12M NPV). "
                        "Net IRR impact of safety investment: approximately neutral to positive."
                    ),
                },
            },
            # ── ROUTE V2 ──────────────────────────────────────────────────
            {
                "variant_id": "ROUTE-V2",
                "rank": 2,
                "label": "Inland Detour — Maximum Terrain Avoidance",
                "description": (
                    "Routes further inland to avoid Volta delta and Lagos "
                    "coastal constraints. Naturally avoids several coastal "
                    "safety conflicts but misses key anchor loads."
                ),
                "total_length_km": 1142.6,
                "vs_straight_line_overhead_pct": 5.8,
                "composite_score": 79.1,
                "coordinates": [
                    [5.350, -4.020],
                    [5.400, -3.500],
                    [5.600, -2.500],
                    [5.800, -1.500],
                    [6.000, -0.800],
                    [6.100, -0.044],
                    [6.270, 0.050],
                    [6.300, 0.700],
                    [6.400, 1.222],
                    [6.500, 1.800],
                    [6.600, 2.406],
                    [6.700, 3.000],
                    [6.800, 3.400],
                    [6.700, 3.700],
                    [6.563, 3.564],
                ],
                "route_geojson": {
                    "type": "LineString",
                    "coordinates": [
                        [-4.020, 5.350],
                        [-3.500, 5.400],
                        [-2.500, 5.600],
                        [-1.500, 5.800],
                        [-0.800, 6.000],
                        [-0.044, 6.100],
                        [0.050, 6.270],
                        [0.700, 6.300],
                        [1.222, 6.400],
                        [1.800, 6.500],
                        [2.406, 6.600],
                        [3.000, 6.700],
                        [3.400, 6.800],
                        [3.700, 6.700],
                        [3.564, 6.563],
                    ],
                },
                "scoring_breakdown": {
                    "capex_score": 71,
                    "terrain_score": 96,
                    "environmental_score": 98,
                    "co_location_score": 61,
                    "anchor_load_coverage": 72,
                    # — NEW —
                    "road_safety_score": 91,
                    "road_safety_score_rationale": (
                        "Inland routing naturally avoids HSC-002 (Tema school), "
                        "HSC-004 (N1 market), HSC-005 (Tema settlement), and "
                        "HSC-008 (Takoradi fuel station). Higher safety score "
                        "than V1 but lower anchor load coverage and revenue. "
                        "Still requires HSC-001, HSC-003 prior action commitments "
                        "at corridor endpoints."
                    ),
                },
                "totals": {
                    "gross_capex_usd": 1218000000,
                    "total_co_location_saving_usd": 109620000,
                    "co_location_saving_pct": 9.0,
                    "net_capex_usd": 1108380000,
                    # — NEW —
                    "total_safety_mitigation_capex_usd": 11545000,
                    "combined_net_capex_including_safety_usd": 1119925000,
                    "safety_capex_as_pct_of_net_capex": 1.0,
                    "weighted_avg_highway_overlap_pct": 54,
                    "anchor_loads_within_15km": 38,
                    "anchor_loads_directly_served": 24,
                    "safety_conflicts_fully_mitigated": 7,
                    "safety_conflicts_avoided_by_routing": 3,
                    "ess4_prior_actions_addressed": 3,
                    "esg_compliance_rating": "FULL — prior actions resolved, fewer conflicts encountered",
                },
                "key_tradeoff": (
                    "Inland routing achieves higher road_safety_score (91 vs 86) "
                    "by naturally avoiding 3 coastal safety conflicts, but loses "
                    "~$55M/year in anchor load revenue vs. ROUTE-V1 and saves "
                    "only $7.7M in safety CAPEX vs. the revenue cost."
                ),
                "financial_indicators": {
                    "estimated_year5_throughput_gwh": 3600,
                    "estimated_year5_revenue_usd": 72000000,
                    "estimated_year5_ebitda_usd": 52000000,
                    "indicative_equity_irr_pct": 11.8,
                    "indicative_project_irr_pct": 8.6,
                    "indicative_payback_years": 14,
                },
            },
            # ── ROUTE V3 ──────────────────────────────────────────────────
            {
                "variant_id": "ROUTE-V3",
                "rank": 3,
                "label": "Shortest Path — Minimum Distance",
                "description": (
                    "Geometric shortest compliant path. Maximises straight-line "
                    "efficiency but passes through most safety conflict zones "
                    "and requires most special construction."
                ),
                "total_length_km": 1058.8,
                "vs_straight_line_overhead_pct": -2.0,
                "composite_score": 71.3,
                "coordinates": [
                    [5.350, -4.020],
                    [5.200, -3.000],
                    [5.100, -1.800],
                    [5.250, -0.700],
                    [5.550, -0.044],
                    [5.800, 0.500],
                    [5.950, 0.800],
                    [6.050, 1.100],
                    [6.137, 1.222],
                    [6.300, 2.000],
                    [6.365, 2.406],
                    [6.380, 3.000],
                    [6.400, 3.564],
                    [6.563, 3.564],
                ],
                "route_geojson": {
                    "type": "LineString",
                    "coordinates": [
                        [-4.020, 5.350],
                        [-3.000, 5.200],
                        [-1.800, 5.100],
                        [-0.700, 5.250],
                        [-0.044, 5.550],
                        [0.500, 5.800],
                        [0.800, 5.950],
                        [1.100, 6.050],
                        [1.222, 6.137],
                        [2.000, 6.300],
                        [2.406, 6.365],
                        [3.000, 6.380],
                        [3.564, 6.400],
                        [3.564, 6.563],
                    ],
                },
                "scoring_breakdown": {
                    "capex_score": 68,
                    "terrain_score": 72,
                    "environmental_score": 88,
                    "co_location_score": 44,
                    "anchor_load_coverage": 79,
                    # — NEW —
                    "road_safety_score": 62,
                    "road_safety_score_rationale": (
                        "Direct coastal route passes through maximum number of "
                        "safety conflict zones — all 10 HSC conflicts encountered. "
                        "Lower score reflects higher safety CAPEX burden and greater "
                        "community exposure along shortest-line corridor. "
                        "Still ESS4 compliant but requires most safety investment."
                    ),
                },
                "totals": {
                    "gross_capex_usd": 1402000000,
                    "total_co_location_saving_usd": 56080000,
                    "co_location_saving_pct": 4.0,
                    "net_capex_usd": 1345920000,
                    # — NEW —
                    "total_safety_mitigation_capex_usd": 19225000,
                    "combined_net_capex_including_safety_usd": 1365145000,
                    "safety_capex_as_pct_of_net_capex": 1.4,
                    "weighted_avg_highway_overlap_pct": 38,
                    "anchor_loads_within_15km": 43,
                    "anchor_loads_directly_served": 29,
                    "safety_conflicts_fully_mitigated": 10,
                    "safety_conflicts_avoided_by_routing": 0,
                    "ess4_prior_actions_addressed": 3,
                    "esg_compliance_rating": "FULL — but highest safety exposure of all variants",
                },
                "key_tradeoff": (
                    "Shortest distance but highest gross CAPEX due to minimal "
                    "co-location. Net CAPEX $179M more than ROUTE-V1 despite "
                    "being 35km shorter. Lowest road_safety_score (62) — "
                    "passes through all 10 safety conflict zones."
                ),
                "financial_indicators": {
                    "estimated_year5_throughput_gwh": 4600,
                    "estimated_year5_revenue_usd": 92000000,
                    "estimated_year5_ebitda_usd": 65000000,
                    "indicative_equity_irr_pct": 12.1,
                    "indicative_project_irr_pct": 8.9,
                    "indicative_payback_years": 13,
                },
            },
            # ── ROUTE V4 ──────────────────────────────────────────────────
            {
                "variant_id": "ROUTE-V4",
                "rank": 4,
                "label": "Maximum Anchor Load Coverage",
                "description": (
                    "Optimised purely to pass within 10km of most anchor loads. "
                    "Highest revenue potential but highest CAPEX. "
                    "Road safety score moderate — encounters more populated "
                    "areas by design."
                ),
                "total_length_km": 1168.3,
                "composite_score": 68.9,
                "coordinates": [
                    [5.350, -4.020],
                    [5.295, -4.003],
                    [5.182, -3.500],
                    [5.100, -2.788],
                    [4.996, -2.200],
                    [5.200, -1.200],
                    [5.500, -0.500],
                    [5.666, -0.044],
                    [6.204, -1.672],
                    [6.270, 0.050],
                    [6.032, 0.607],
                    [6.137, 1.222],
                    [6.425, 2.406],
                    [6.420, 2.700],
                    [6.438, 3.400],
                    [6.438, 3.989],
                    [6.427, 3.987],
                    [6.449, 3.988],
                    [6.563, 3.564],
                ],
                "route_geojson": {
                    "type": "LineString",
                    "coordinates": [
                        [-4.020, 5.350],
                        [-4.003, 5.295],
                        [-3.500, 5.182],
                        [-2.788, 5.100],
                        [-2.200, 4.996],
                        [-1.200, 5.200],
                        [-0.500, 5.500],
                        [-0.044, 5.666],
                        [-1.672, 6.204],
                        [0.050, 6.270],
                        [0.607, 6.032],
                        [1.222, 6.137],
                        [2.406, 6.425],
                        [2.700, 6.420],
                        [3.400, 6.438],
                        [3.989, 6.438],
                        [3.987, 6.427],
                        [3.988, 6.449],
                        [3.564, 6.563],
                    ],
                },
                "scoring_breakdown": {
                    "capex_score": 64,
                    "terrain_score": 78,
                    "environmental_score": 85,
                    "co_location_score": 65,
                    "anchor_load_coverage": 96,
                    # — NEW —
                    "road_safety_score": 74,
                    "road_safety_score_rationale": (
                        "Passes through highest-density populated zones by design "
                        "to maximise anchor load access. Encounters 8 of 10 HSC "
                        "conflicts. All mitigated but higher community exposure "
                        "increases ESS4 monitoring burden. Good score given the "
                        "trade-off with anchor load coverage objective."
                    ),
                },
                "totals": {
                    "gross_capex_usd": 1487000000,
                    "total_co_location_saving_usd": 193310000,
                    "co_location_saving_pct": 13.0,
                    "net_capex_usd": 1293690000,
                    # — NEW —
                    "total_safety_mitigation_capex_usd": 17445000,
                    "combined_net_capex_including_safety_usd": 1311135000,
                    "safety_capex_as_pct_of_net_capex": 1.3,
                    "weighted_avg_highway_overlap_pct": 65,
                    "anchor_loads_within_15km": 54,
                    "anchor_loads_directly_served": 38,
                    "safety_conflicts_fully_mitigated": 8,
                    "safety_conflicts_avoided_by_routing": 2,
                    "ess4_prior_actions_addressed": 3,
                    "esg_compliance_rating": "FULL — highest anchor load coverage, moderate safety exposure",
                },
                "key_tradeoff": (
                    "Highest anchor load coverage and revenue ceiling ($116M/year), "
                    "best equity IRR (14.8%), but $127M more CAPEX than ROUTE-V1 "
                    "and moderate road_safety_score (74) due to maximising "
                    "populated-area penetration."
                ),
                "financial_indicators": {
                    "estimated_year5_throughput_gwh": 5800,
                    "estimated_year5_revenue_usd": 116000000,
                    "estimated_year5_ebitda_usd": 88000000,
                    "indicative_equity_irr_pct": 14.8,
                    "indicative_project_irr_pct": 10.6,
                    "indicative_payback_years": 11,
                },
            },
            # ── ROUTE V5 ──────────────────────────────────────────────────
            {
                "variant_id": "ROUTE-V5",
                "rank": 5,
                "label": "Minimum Environmental Footprint",
                "description": (
                    "Maximises distance from all sensitive areas. Lowest "
                    "environmental risk rating. Also achieves highest road "
                    "safety score by routing away from all populated zones — "
                    "but misses most anchor loads."
                ),
                "total_length_km": 1198.7,
                "composite_score": 64.2,
                "coordinates": [
                    [5.350, -4.020],
                    [5.500, -3.200],
                    [5.700, -2.000],
                    [5.900, -0.800],
                    [6.000, -0.044],
                    [6.300, 0.300],
                    [6.500, 0.800],
                    [6.400, 1.222],
                    [6.600, 1.800],
                    [6.700, 2.406],
                    [6.800, 3.000],
                    [6.900, 3.400],
                    [6.700, 3.700],
                    [6.563, 3.564],
                ],
                "route_geojson": {
                    "type": "LineString",
                    "coordinates": [
                        [-4.020, 5.350],
                        [-3.200, 5.500],
                        [-2.000, 5.700],
                        [-0.800, 5.900],
                        [-0.044, 6.000],
                        [0.300, 6.300],
                        [0.800, 6.500],
                        [1.222, 6.400],
                        [1.800, 6.600],
                        [2.406, 6.700],
                        [3.000, 6.800],
                        [3.400, 6.900],
                        [3.700, 6.700],
                        [3.564, 6.563],
                    ],
                },
                "scoring_breakdown": {
                    "capex_score": 72,
                    "terrain_score": 88,
                    "environmental_score": 99,
                    "co_location_score": 55,
                    "anchor_load_coverage": 61,
                    # — NEW —
                    "road_safety_score": 97,
                    "road_safety_score_rationale": (
                        "Northern inland routing avoids all 10 HSC conflict zones "
                        "by maintaining maximum distance from populated coastal strip. "
                        "Highest road_safety_score of all variants. However, this "
                        "is the recommended route ONLY if 'max_safety' priority "
                        "mode is selected — under 'balance' mode the anchor load "
                        "and revenue penalty is too high to justify."
                    ),
                },
                "totals": {
                    "gross_capex_usd": 1154000000,
                    "total_co_location_saving_usd": 138480000,
                    "co_location_saving_pct": 12.0,
                    "net_capex_usd": 1015520000,
                    # — NEW —
                    "total_safety_mitigation_capex_usd": 0,
                    "combined_net_capex_including_safety_usd": 1015520000,
                    "safety_capex_as_pct_of_net_capex": 0.0,
                    "weighted_avg_highway_overlap_pct": 59,
                    "anchor_loads_within_15km": 34,
                    "anchor_loads_directly_served": 21,
                    "safety_conflicts_fully_mitigated": 0,
                    "safety_conflicts_avoided_by_routing": 10,
                    "ess4_prior_actions_addressed": 3,
                    "esg_compliance_rating": (
                        "FULL — zero safety conflicts encountered. "
                        "Recommended under 'max_safety' priority mode."
                    ),
                },
                "key_tradeoff": (
                    "Lowest permitting risk (~14 months ESIA vs. 20 months base), "
                    "zero safety CAPEX burden, highest road_safety_score (97). "
                    "However misses 13 anchor loads vs. ROUTE-V1 and loses "
                    "$34M/year EBITDA. Recommended ONLY under max_safety priority."
                ),
                "financial_indicators": {
                    "estimated_year5_throughput_gwh": 3100,
                    "estimated_year5_revenue_usd": 62000000,
                    "estimated_year5_ebitda_usd": 44000000,
                    "indicative_equity_irr_pct": 11.2,
                    "indicative_project_irr_pct": 7.9,
                    "indicative_payback_years": 15,
                },
            },
        ],
        # ================================================================
        # RECOMMENDED ROUTE
        # Updated rationale includes road safety dimension explicitly.
        # ================================================================
        "recommended_route": {
            "variant_id": "ROUTE-V1",
            "rationale": (
                "ROUTE-V1 delivers the best risk-adjusted outcome across all "
                "six scoring dimensions including the new road_safety_score (86). "
                "It achieves 13.5% co-location savings ($182M), serves 31 anchor "
                "loads directly, generates 14.2% equity IRR, and achieves full "
                "ESS4 compliance by addressing all 3 CRITICAL prior actions. "
                "Safety CAPEX of $19.2M (1.6% of net CAPEX) is offset by "
                "estimated DFI financing cost improvement and reduced delay risk, "
                "making the net IRR impact approximately neutral. ROUTE-V5 is "
                "recommended instead if 'max_safety' priority mode is selected."
            ),
            "conditions": [
                # — Original environmental conditions —
                "ENV-001 northern detour (Ankasa) must be incorporated into final engineering design",
                "WET-001 Ramsar notification must be filed before construction mobilisation",
                "Underground cable commitment for Lagos urban section (3.8 km) confirmed in project scope",
                "Pile foundation design for Volta delta (22 km) commissioned as priority geotechnical study",
                # — NEW safety prior action conditions —
                "HSC-001: Abidjan junction redesign (signalised roundabout) approved before Phase 1 construction",
                "HSC-002: Tema school zone mitigation installed and construction halt confirmed before Phase 1 construction",
                "HSC-003: Ghana-Togo border crossing redesign bilateral agreement with ALCOMA initiated before Phase 2 construction",
                "Road Safety Action Plan (RSAP) disclosed and approved by DFI appraisal teams before financial close",
                "Independent Road Safety Audit commissioned for full 1,080 km corridor before detailed design freeze",
            ],
        },
        # ================================================================
        # PHASING RECOMMENDATION
        # Updated: each phase now includes safety_interventions_required
        # and safety_prior_actions_before_construction.
        # ================================================================
        "phasing_recommendation": {
            "phase_1": {
                "segments": ["V1-SEG-001", "V1-SEG-003"],
                "rationale": (
                    "Lowest terrain difficulty and highest highway overlap — "
                    "fastest to construct and earliest revenue."
                ),
                "combined_length_km": 480,
                "combined_net_capex_usd": 490610000,
                "anchor_loads_activated": 12,
                "estimated_year3_revenue_usd": 38000000,
                # — NEW —
                "safety_capex_this_phase_usd": 8180000,
                "combined_net_capex_including_safety_usd": 498790000,
                "safety_prior_actions_before_construction": [
                    {
                        "conflict_id": "HSC-001",
                        "action": "Abidjan junction redesign — signalised roundabout approved by Côte d'Ivoire Ministry of Transport",
                        "deadline": "Before Phase 1 construction mobilisation",
                        "responsible_party": "ALCOMA + Côte d'Ivoire Ministry of Transport",
                        "capex_usd": 3500000,
                    },
                    {
                        "conflict_id": "HSC-002",
                        "action": "Tema school pedestrian crossing + speed tables + fencing installed. Construction halt on road-facing classroom confirmed with Ghana Education Service.",
                        "deadline": "Before Phase 1 construction mobilisation",
                        "responsible_party": "ALCOMA + Ghana NRSA + Ghana Education Service",
                        "capex_usd": 850000,
                    },
                ],
                "safety_interventions_during_phase": [
                    "HSC-004: N1 market zone — off-road trading area + rumble strips + lighting ($650K)",
                    "HSC-005: Tema-Accra settlement — footpath + kerb + drainage + RAP ($1.8M)",
                    "HSC-008: Takoradi fuel station — deceleration/acceleration lanes ($280K)",
                ],
                "dfI_financing_gate": (
                    "HSC-001 and HSC-002 prior actions must be approved and "
                    "confirmed in writing before DFI drawdown on Phase 1 is permitted."
                ),
            },
            "phase_2": {
                "segments": ["V1-SEG-002"],
                "rationale": (
                    "Requires longest lead time for Volta delta geotechnical "
                    "design and Ramsar permitting."
                ),
                "combined_length_km": 188,
                "combined_net_capex_usd": 206290000,
                "anchor_loads_activated": 9,
                "estimated_incremental_revenue_usd": 28000000,
                # — NEW —
                "safety_capex_this_phase_usd": 7200000,
                "combined_net_capex_including_safety_usd": 213490000,
                "safety_prior_actions_before_construction": [
                    {
                        "conflict_id": "HSC-003",
                        "action": "Ghana-Togo border crossing redesign — pedestrian footbridge + physical separation + full lighting. Bilateral ALCOMA agreement signed.",
                        "deadline": "Before Phase 2 construction mobilisation",
                        "responsible_party": "ALCOMA + Ghana Highways + Togo Ministry of Infrastructure",
                        "capex_usd": 7200000,
                    },
                ],
                "safety_interventions_during_phase": [],
                "dfI_financing_gate": (
                    "HSC-003 bilateral agreement must be signed and border "
                    "redesign design approved before DFI drawdown on Phase 2."
                ),
            },
            "phase_3": {
                "segments": ["V1-SEG-004"],
                "rationale": (
                    "Lagos segment has highest anchor load value but requires "
                    "most complex urban permitting."
                ),
                "combined_length_km": 426,
                "combined_net_capex_usd": 469920000,
                "anchor_loads_activated": 10,
                "estimated_incremental_revenue_usd": 55000000,
                # — NEW —
                "safety_capex_this_phase_usd": 3845000,
                "combined_net_capex_including_safety_usd": 473765000,
                "safety_prior_actions_before_construction": [],
                "safety_interventions_during_phase": [
                    "HSC-007: Lagos truck layby — formal rest area 50 bays + FRSC MOU ($3.8M)",
                    "HSC-010: Lagos road works — TTM plan deploy immediately + night lighting ($45K)",
                ],
                "dfI_financing_gate": (
                    "No additional safety prior actions required for Phase 3. "
                    "Ongoing ESS4 monitoring through ESMP compliance reporting."
                ),
            },
        },
        # ================================================================
        # ROAD SAFETY PERFORMANCE SUMMARY
        # New top-level section summarising safety outcomes across
        # all routes — enables quick DFI appraisal team review.
        # ================================================================
        "road_safety_performance_summary": {
            "total_safety_conflicts_identified": 10,
            "total_safety_conflicts_by_severity": {
                "CRITICAL": 3,
                "HIGH": 4,
                "MEDIUM": 2,
                "LOW": 1,
            },
            "ess4_prior_actions_count": 3,
            "ess4_prior_actions_resolved_in_recommended_route": 3,
            "total_estimated_population_protected": 54400,
            "road_safety_scores_by_variant": {
                "ROUTE-V1": 86,
                "ROUTE-V2": 91,
                "ROUTE-V3": 62,
                "ROUTE-V4": 74,
                "ROUTE-V5": 97,
            },
            "recommended_variant_safety_capex_usd": 19225000,
            "recommended_variant_safety_capex_pct_of_net_capex": 1.6,
            "max_safety_recommended_variant": "ROUTE-V5",
            "balance_recommended_variant": "ROUTE-V1",
            "road_safety_action_plan_required": True,
            "independent_road_safety_audit_required": True,
            "national_road_safety_authorities_to_engage": [
                "Côte d'Ivoire — OSER (Office de la Sécurité Routière)",
                "Ghana — NRSA (National Road Safety Authority)",
                "Togo — Direction de la Sécurité Routière",
                "Benin — ANASER (Agence Nationale de Sécurité Routière)",
                "Nigeria — FRSC (Federal Road Safety Corps)",
            ],
            "note": (
                "Road safety scores and CAPEX figures are derived from "
                "infrastructure_detection (DET-RS-001 to DET-RS-010) and "
                "environmental_constraints (HSC-001 to HSC-010) tool outputs. "
                "All 5 variants achieve full ESS4 compliance when recommended "
                "mitigations are applied. Safety CAPEX of 1.0–1.6% of net CAPEX "
                "across variants represents a minor cost addition with significant "
                "risk reduction and DFI financing benefit."
            ),
        },
        # ================================================================
        # VARIANTS ELIMINATED (updated count)
        # ================================================================
        "variants_eliminated": {
            "total_eliminated": 17,
            "reasons": {
                "hard_environmental_constraint_violation": 8,
                # — NEW —
                "hard_safety_constraint_violation": 3,
                "dominated_on_all_metrics": 4,
                "engineering_infeasible_turning_radius": 2,
            },
            "safety_eliminations_detail": (
                "3 variants eliminated for passing through NGZ-RS-001 (Tema school), "
                "NGZ-RS-002 (Ghana-Togo border), or NGZ-RS-003 (Abidjan junction) "
                "without confirmed mitigation design commitment. "
                "These are treated as hard constraints equivalent to IUCN Category II "
                "protected areas under the cost grid weighting."
            ),
        },
        # ================================================================
        # OUTPUT URIS (updated to include safety outputs)
        # ================================================================
        "output_uris": {
            # — Original —
            "all_routes_geojson": (
                "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                "routes/all_75_variants.geojson"
            ),
            "top5_routes_geojson": (
                "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                "routes/top5_routes.geojson"
            ),
            "recommended_route_geojson": (
                "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                "routes/ROUTE_V1_recommended.geojson"
            ),
            "cost_grid_raster": (
                "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                "routes/weighted_cost_grid.tif"
            ),
            "phasing_map_geojson": (
                "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                "routes/phasing_segments.geojson"
            ),
            "comparison_report_csv": (
                "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                "routes/route_comparison_matrix.csv"
            ),
            # — NEW safety outputs —
            "safety_cost_grid_raster": (
                "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                "routes/safety_penalty_layer.tif"
            ),
            "road_safety_scores_geojson": (
                "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                "routes/road_safety_scores_by_variant.geojson"
            ),
            "safety_capex_breakdown_csv": (
                "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                "routes/safety_capex_by_segment.csv"
            ),
            "max_safety_route_geojson": (
                "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                "routes/ROUTE_V5_max_safety.geojson"
            ),
            "rsap_template_json": (
                "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                "safety/rsap_template.json"
            ),
            "dfi_safety_compliance_report_pdf": (
                "s3://corridor-platform/data/ABIDJAN_LAGOS_CORRIDOR/"
                "safety/ess4_compliance_report.pdf"
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
