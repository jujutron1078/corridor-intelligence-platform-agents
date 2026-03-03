import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import CostEstimationInput


@tool("generate_cost_estimates", description=TOOL_DESCRIPTION)
def generate_cost_estimates_tool(
    payload: CostEstimationInput, runtime: ToolRuntime
) -> Command:
    """Calculates total project CAPEX ($730M-$1,005M) and annual OPEX."""

    # In a real-world scenario, this tool would:
    # 1. Use unit costs (e.g., $450k/km for 400kV line, $15M per substation).
    # 2. Calculate OPEX as a percentage (typically 1-2%) of total CAPEX.
    # 3. Adjust for local labor and logistics costs in each country.

    response = {
        "corridor_id": "AL_CORRIDOR_POC_001",
        "cost_basis": {
            "pricing_date": "Q1 2026",
            "currency": "USD",
            "contingency_pct": 15.0,
            "unit_cost_source": "WAPP Regional Transmission Cost Database 2024 + AfDB West Africa Infrastructure Cost Survey 2023",
            "regional_adjustments": {
                "cote_divoire": "Base rate (CFA zone, stable logistics)",
                "ghana": "Base rate +3% (port congestion premium)",
                "togo": "Base rate +5% (limited heavy haulage routes)",
                "benin": "Base rate +5% (limited heavy haulage routes)",
                "nigeria": "Base rate +12% (security, local content requirements, Lagos urban premium)",
            },
            "colocation_savings_applied": True,
            "colocation_savings_basis": (
                "Savings quantified per segment based on highway overlap % from "
                "quantify_colocation_benefits output. Applied to civil works, "
                "access roads, land clearing, and logistics line items only."
            ),
        },

        # ================================================================
        # UNIT COST REFERENCE TABLE
        # ================================================================
        "unit_costs_usd": {
            "transmission_lines": {
                "400kv_quad_bundle_accc_per_km": 1_850_000,
                "330kv_twin_bundle_aaac_per_km": 980_000,
                "161kv_twin_bundle_acsr_per_km": 520_000,
                "161kv_single_acsr_per_km": 320_000,
                "33kv_xlpe_underground_per_km": 1_200_000,
                "132kv_xlpe_underground_per_km": 2_800_000,
                "400kv_xlpe_underground_per_km": 3_900_000,
            },
            "substations": {
                "400kv_hub_per_bay": 18_000_000,
                "330kv_hub_per_bay": 11_500_000,
                "161kv_substation_per_bay": 6_200_000,
                "33kv_distribution_substation": 3_800_000,
                "132kv_substation_upgrade_per_transformer": 14_000_000,
            },
            "reactive_power_compensation": {
                "shunt_reactor_per_mvar": 45_000,
                "svc_per_mvar": 95_000,
                "statcom_per_mvar": 120_000,
            },
            "ancillary": {
                "scada_per_substation": 850_000,
                "fiber_optic_per_km": 28_000,
                "border_crossing_package": 4_500_000,
                "esia_per_segment": 2_200_000,
                "resettlement_per_household": 18_000,
            },
        },

        # ================================================================
        # CAPEX BY SEGMENT
        # ================================================================
        "capex_by_segment": [

            # ---- BACKBONE SEGMENTS ----
            {
                "segment_id": "SEG_BB_001",
                "name": "Abidjan Hub — Takoradi Hub",
                "phase": "Phase 2",
                "route_length_km": 382.0,
                "voltage_kv": 330,
                "conductor": "AAAC Twin-bundle",
                "colocation_pct": 55.0,

                "line_costs_usd": {
                    "overhead_stringing": 267_540_000,   # 273km overhead @ $980K/km
                    "underground_xlpe_section": 46_800_000,  # 12km Ankasa deviation @ $3.9M/km (330kV)
                    "tower_foundations_coastal": 8_400_000,  # Half Assini pile foundations (3 locations)
                    "subtotal": 322_740_000,
                },
                "substation_costs_usd": {
                    "abidjan_vridi_hub_bays": 34_500_000,   # 3 x 330kV bays
                    "takoradi_aboadze_hub_bays": 23_000_000, # 2 x 330kV bays
                    "mid_point_switching_station": 9_200_000,
                    "subtotal": 66_700_000,
                },
                "ancillary_costs_usd": {
                    "reactive_power_compensation": 8_100_000,  # Shunt reactors + SVCs
                    "scada_and_fiber": 12_696_000,             # 382km fiber @ $28K/km + 3 SCADA nodes
                    "border_crossing_package": 4_500_000,      # CI/Ghana Elubo crossing
                    "esia_and_permitting": 4_400_000,          # 2 segments (CI + Ghana)
                    "resettlement": 3_240_000,                 # Est. 180 households
                    "subtotal": 32_936_000,
                },
                "subtotal_before_contingency_usd": 422_376_000,
                "colocation_savings_usd": -56_200_000,   # 55% overlap — civil + access roads
                "subtotal_after_savings_usd": 366_176_000,
                "contingency_15pct_usd": 54_926_000,
                "total_segment_capex_usd": 421_102_000,
            },

            {
                "segment_id": "SEG_BB_002",
                "name": "Takoradi Hub — Tema/Accra Hub",
                "phase": "Phase 1",
                "route_length_km": 235.0,
                "voltage_kv": 330,
                "conductor": "AAAC Twin-bundle Double-circuit",
                "colocation_pct": 68.0,

                "line_costs_usd": {
                    "overhead_stringing_new": 115_150_000,  # 235km @ $980K/km x 1 circuit (second reuses towers)
                    "existing_tower_reuse_saving": -45_000_000,  # 70% towers reusable
                    "head_frame_replacement": 16_450_000,   # 70% towers need head-frame swap
                    "subtotal": 86_600_000,
                },
                "substation_costs_usd": {
                    "takoradi_aboadze_330kv_bays": 23_000_000,
                    "tema_industrial_330kv_bays": 34_500_000,  # 3 bays (N-1-1 double-circuit)
                    "tema_161kv_transformer_interface": 12_400_000,
                    "subtotal": 69_900_000,
                },
                "ancillary_costs_usd": {
                    "reactive_power_compensation": 5_400_000,
                    "scada_and_fiber": 8_430_000,
                    "esia_and_permitting": 2_200_000,
                    "resettlement": 1_800_000,   # Est. 100 households
                    "subtotal": 17_830_000,
                },
                "subtotal_before_contingency_usd": 174_330_000,
                "colocation_savings_usd": -28_900_000,  # 68% overlap
                "subtotal_after_savings_usd": 145_430_000,
                "contingency_15pct_usd": 21_815_000,
                "total_segment_capex_usd": 167_245_000,
            },

            {
                "segment_id": "SEG_BB_003",
                "name": "Tema Hub — Lomé Hub",
                "phase": "Phase 2",
                "route_length_km": 178.0,
                "voltage_kv": 330,
                "conductor": "AAAC Twin-bundle",
                "colocation_pct": 72.0,

                "line_costs_usd": {
                    "overhead_stringing": 145_360_000,    # 164km overhead @ $980K/km
                    "underground_xlpe_section": 54_600_000,  # 14km Aflao/Lomé urban @ $3.9M/km
                    "subtotal": 199_960_000,
                },
                "substation_costs_usd": {
                    "tema_industrial_additional_bays": 11_500_000,
                    "tokoin_lome_330kv_hub": 46_000_000,  # 4 bays (new hub)
                    "subtotal": 57_500_000,
                },
                "ancillary_costs_usd": {
                    "reactive_power_compensation": 4_800_000,
                    "scada_and_fiber": 6_424_000,
                    "border_crossing_package": 4_500_000,   # Ghana/Togo Aflao crossing
                    "esia_and_permitting": 4_400_000,
                    "resettlement": 2_160_000,   # Est. 120 households
                    "subtotal": 22_284_000,
                },
                "subtotal_before_contingency_usd": 279_744_000,
                "colocation_savings_usd": -38_400_000,  # 72% overlap
                "subtotal_after_savings_usd": 241_344_000,
                "contingency_15pct_usd": 36_202_000,
                "total_segment_capex_usd": 277_546_000,
            },

            {
                "segment_id": "SEG_BB_004",
                "name": "Lomé Hub — Cotonou Hub",
                "phase": "Phase 2",
                "route_length_km": 142.0,
                "voltage_kv": 330,
                "conductor": "AAAC Single 400mm²",
                "colocation_pct": 78.0,

                "line_costs_usd": {
                    "overhead_stringing": 130_256_000,   # 136km overhead @ $980K/km
                    "underground_xlpe_section": 7_200_000,   # 6km Porto-Novo urban
                    "subtotal": 137_456_000,
                },
                "substation_costs_usd": {
                    "tokoin_lome_additional_bays": 11_500_000,
                    "maria_gleta_cotonou_330kv_hub": 34_500_000,  # 3 bays
                    "porto_novo_midpoint_switching": 8_400_000,
                    "subtotal": 54_400_000,
                },
                "ancillary_costs_usd": {
                    "reactive_power_compensation": 3_600_000,
                    "scada_and_fiber": 5_276_000,
                    "border_crossing_package": 4_500_000,   # Togo/Benin crossing
                    "esia_and_permitting": 4_400_000,
                    "resettlement": 1_440_000,   # Est. 80 households
                    "subtotal": 19_216_000,
                },
                "subtotal_before_contingency_usd": 211_072_000,
                "colocation_savings_usd": -35_600_000,  # 78% overlap — highest on corridor
                "subtotal_after_savings_usd": 175_472_000,
                "contingency_15pct_usd": 26_321_000,
                "total_segment_capex_usd": 201_793_000,
            },

            {
                "segment_id": "SEG_BB_005",
                "name": "Cotonou Hub — Lagos/Lekki Hub",
                "phase": "Phase 1",
                "route_length_km": 152.0,
                "voltage_kv": 400,
                "conductor": "ACCC Quad-bundle (Double-circuit, separate routes)",
                "colocation_pct": 62.0,
                "note": "Most expensive segment — 400kV, separate-route double-circuit, 22km Lagos underground",

                "line_costs_usd": {
                    "overhead_stringing_circuit_1": 140_600_000,  # 130km @ $1.85M/km (400kV)
                    "overhead_stringing_circuit_2": 140_600_000,  # Separate route (N-1-1 requirement)
                    "underground_xlpe_400kv_lagos": 85_800_000,   # 22km @ $3.9M/km x 2 circuits
                    "subtotal": 367_000_000,
                },
                "substation_costs_usd": {
                    "lekki_400kv_hub_phase_1a": 145_000_000,  # Full hub — 500MW Phase 1A
                    "maria_gleta_400_330kv_interface": 36_000_000,  # 2 x 400kV bays
                    "badagry_midpoint_statcom": 18_000_000,
                    "subtotal": 199_000_000,
                },
                "ancillary_costs_usd": {
                    "reactive_power_compensation": 14_400_000,  # SVCs + STATCOM at 3 locations
                    "scada_and_fiber": 9_056_000,
                    "border_crossing_package": 4_500_000,   # Benin/Nigeria Seme crossing
                    "esia_and_permitting": 4_400_000,
                    "resettlement": 3_600_000,   # Est. 200 households (two separate routes)
                    "nigeria_local_content_levy": 12_000_000,  # 2% of Nigeria-side CAPEX
                    "subtotal": 47_956_000,
                },
                "subtotal_before_contingency_usd": 613_956_000,
                "colocation_savings_usd": -38_200_000,  # 62% overlap — lower due to separate circuits
                "subtotal_after_savings_usd": 575_756_000,
                "contingency_15pct_usd": 86_363_000,
                "total_segment_capex_usd": 662_119_000,
            },

            # ---- SPUR SEGMENTS ----
            {
                "segment_id": "SEG_SP_001",
                "name": "Kumasi Hub — Obuasi Gold Mine Spur",
                "phase": "Phase 1",
                "route_length_km": 98.0,
                "voltage_kv": 161,
                "conductor": "ACSR Zebra Twin-bundle Double-circuit",
                "colocation_pct": 38.0,

                "line_costs_usd": {
                    "overhead_stringing": 101_920_000,   # 98km x 2 circuits @ $520K/km
                    "subtotal": 101_920_000,
                },
                "substation_costs_usd": {
                    "kumasi_161kv_bay_addition": 8_000_000,
                    "obuasi_mine_receiving_substation": 24_800_000,  # 4 x 161kV bays
                    "subtotal": 32_800_000,
                },
                "ancillary_costs_usd": {
                    "scada_and_fiber": 3_494_000,
                    "obuasi_forest_reserve_esia": 2_800_000,  # Category B assessment
                    "resettlement": 900_000,    # Est. 50 households
                    "subtotal": 7_194_000,
                },
                "subtotal_before_contingency_usd": 141_914_000,
                "colocation_savings_usd": -8_200_000,  # 38% overlap — partial agri road use
                "subtotal_after_savings_usd": 133_714_000,
                "contingency_15pct_usd": 20_057_000,
                "total_segment_capex_usd": 153_771_000,
            },

            {
                "segment_id": "SEG_SP_002",
                "name": "Akuse Hub — Volta Agricultural Belt Spur (Conditional)",
                "phase": "Phase 2",
                "route_length_km": 35.0,
                "voltage_kv": 161,
                "conductor": "ACSR Panther Single",
                "colocation_pct": 22.0,
                "conditional": True,

                "line_costs_usd": {
                    "overhead_stringing": 11_200_000,
                    "elevated_tower_floodplain_section": 3_840_000,  # 8km elevated design
                    "subtotal": 15_040_000,
                },
                "substation_costs_usd": {
                    "akuse_161kv_t_off": 4_960_000,
                    "weta_zone_161_33kv_substation": 12_400_000,
                    "elevated_platform_civil_works": 1_800_000,
                    "subtotal": 19_160_000,
                },
                "ancillary_costs_usd": {
                    "temporary_access_road": 800_000,
                    "scada_and_fiber": 1_780_000,
                    "esia_and_permitting": 1_800_000,
                    "resettlement": 540_000,   # Est. 30 households
                    "subtotal": 4_920_000,
                },
                "subtotal_before_contingency_usd": 39_120_000,
                "colocation_savings_usd": -1_800_000,  # 22% overlap — minimal
                "subtotal_after_savings_usd": 37_320_000,
                "contingency_15pct_usd": 5_598_000,
                "total_segment_capex_usd": 42_918_000,
            },

            {
                "segment_id": "SEG_SP_003",
                "name": "Mampong Hub — Lithium Site Spur (Conditional)",
                "phase": "Phase 3",
                "route_length_km": 44.0,
                "voltage_kv": 161,
                "conductor": "ACSR Zebra Single (Twin-bundle at full production)",
                "colocation_pct": 18.0,
                "conditional": True,

                "line_costs_usd": {
                    "overhead_stringing": 14_080_000,
                    "subtotal": 14_080_000,
                },
                "substation_costs_usd": {
                    "mampong_161kv_t_off": 4_960_000,
                    "lithium_site_receiving_substation": 12_400_000,
                    "subtotal": 17_360_000,
                },
                "ancillary_costs_usd": {
                    "scada_and_fiber": 2_082_000,
                    "esia_category_b": 2_200_000,   # Greenfield route — full Category B
                    "resettlement": 1_080_000,   # Est. 60 households — agri land
                    "subtotal": 5_362_000,
                },
                "subtotal_before_contingency_usd": 36_802_000,
                "colocation_savings_usd": -900_000,   # 18% overlap — minimal
                "subtotal_after_savings_usd": 35_902_000,
                "contingency_15pct_usd": 5_385_000,
                "total_segment_capex_usd": 41_287_000,
            },

            # ---- DISTRIBUTION REINFORCEMENTS ----
            {
                "segment_id": "SEG_DR_001",
                "name": "Lomé Industrial 161kV Ring",
                "phase": "Phase 1",
                "route_length_km": 18.0,
                "voltage_kv": 161,
                "conductor": "XLPE underground (port) + ACSR overhead",
                "colocation_pct": 80.0,

                "line_costs_usd": {
                    "xlpe_underground_port_section": 8_400_000,  # 7km @ $1.2M/km
                    "acsr_overhead_sections": 5_720_000,          # 11km @ $520K/km
                    "subtotal": 14_120_000,
                },
                "substation_costs_usd": {
                    "ring_main_switching_points_3x": 11_400_000,
                    "subtotal": 11_400_000,
                },
                "ancillary_costs_usd": {
                    "scada_and_fiber": 1_354_000,
                    "permitting_togo": 800_000,
                    "subtotal": 2_154_000,
                },
                "subtotal_before_contingency_usd": 27_674_000,
                "colocation_savings_usd": -4_800_000,
                "subtotal_after_savings_usd": 22_874_000,
                "contingency_15pct_usd": 3_431_000,
                "total_segment_capex_usd": 26_305_000,
            },

            {
                "segment_id": "SEG_DR_002",
                "name": "Zone Industrielle Cotonou 33kV Feeder",
                "phase": "Phase 2",
                "route_length_km": 8.0,
                "voltage_kv": 33,
                "conductor": "XLPE 300mm² underground",
                "colocation_pct": 60.0,

                "line_costs_usd": {
                    "xlpe_underground": 9_600_000,   # 8km @ $1.2M/km
                    "subtotal": 9_600_000,
                },
                "substation_costs_usd": {
                    "cotonou_industrial_33kv_substation": 3_800_000,
                    "statcom_50mvar": 6_000_000,
                    "subtotal": 9_800_000,
                },
                "ancillary_costs_usd": {
                    "scada": 850_000,
                    "permitting_benin": 600_000,
                    "subtotal": 1_450_000,
                },
                "subtotal_before_contingency_usd": 20_850_000,
                "colocation_savings_usd": -2_400_000,
                "subtotal_after_savings_usd": 18_450_000,
                "contingency_15pct_usd": 2_768_000,
                "total_segment_capex_usd": 21_218_000,
            },

            {
                "segment_id": "SEG_DR_003",
                "name": "Abidjan Vridi 225/11kV Industrial Substation Upgrade",
                "phase": "Phase 2",
                "route_length_km": 6.0,
                "voltage_kv": 225,
                "conductor": "XLPE 400mm² underground",
                "colocation_pct": 85.0,

                "line_costs_usd": {
                    "xlpe_underground": 7_200_000,   # 6km @ $1.2M/km
                    "subtotal": 7_200_000,
                },
                "substation_costs_usd": {
                    "vridi_225_11kv_new_transformer_bays": 23_000_000,
                    "subtotal": 23_000_000,
                },
                "ancillary_costs_usd": {
                    "scada": 850_000,
                    "permitting_ci": 500_000,
                    "subtotal": 1_350_000,
                },
                "subtotal_before_contingency_usd": 31_550_000,
                "colocation_savings_usd": -4_200_000,
                "subtotal_after_savings_usd": 27_350_000,
                "contingency_15pct_usd": 4_103_000,
                "total_segment_capex_usd": 31_453_000,
            },

            {
                "segment_id": "SEG_DR_004",
                "name": "Sagamu Interchange 132kV Substation Upgrade",
                "phase": "Phase 2",
                "route_length_km": 0.0,
                "voltage_kv": 132,
                "conductor": "N/A — substation upgrade only",
                "colocation_pct": 0.0,

                "line_costs_usd": {
                    "subtotal": 0,
                },
                "substation_costs_usd": {
                    "transformer_replacement_2x_60mva": 28_000_000,
                    "subtotal": 28_000_000,
                },
                "ancillary_costs_usd": {
                    "scada_upgrade": 850_000,
                    "permitting_nerc_nigeria": 600_000,
                    "subtotal": 1_450_000,
                },
                "subtotal_before_contingency_usd": 29_450_000,
                "colocation_savings_usd": 0,
                "subtotal_after_savings_usd": 29_450_000,
                "contingency_15pct_usd": 4_418_000,
                "total_segment_capex_usd": 33_868_000,
            },
        ],

        # ================================================================
        # CONSOLIDATED COST SUMMARY
        # ================================================================
        "cost_summary": {
            "line_costs_usd": 468_916_000,
            "substation_costs_usd": 362_060_000,
            "reactive_power_compensation_usd": 36_300_000,
            "scada_and_fiber_usd": 50_442_000,
            "esia_resettlement_and_permitting_usd": 47_160_000,
            "local_content_and_regulatory_levies_usd": 12_000_000,
            "other_civil_and_eia_usd": 59_160_000,
            "subtotal_before_contingency_usd": 1_036_038_000,
            "total_colocation_savings_usd": -219_600_000,
            "subtotal_after_colocation_savings_usd": 816_438_000,
            "contingency_15pct_usd": 122_466_000,
            "total_capex_usd": 938_904_000,

            "annual_opex_usd": {
                "transmission_line_maintenance": 8_200_000,   # 0.6% of line CAPEX
                "substation_maintenance": 5_400_000,          # 1.5% of substation CAPEX
                "scada_and_it_systems": 1_800_000,
                "insurance": 4_700_000,                       # 0.5% of total CAPEX
                "staffing_corridor_operations": 3_600_000,    # 5-country ops centre
                "reactive_power_compensation_maintenance": 900_000,
                "total_annual_opex_usd": 24_600_000,
            },
        },

        # ================================================================
        # COST BY PHASE
        # ================================================================
        "cost_by_phase": {
            "phase_1": {
                "segments": ["SEG_BB_002", "SEG_BB_005", "SEG_SP_001", "SEG_DR_001"],
                "total_capex_usd": 520_000_000,
                "pct_of_total": "55.4%",
                "rationale": "Phase 1 is most expensive due to 400kV Lagos segment and Lekki hub.",
            },
            "phase_2": {
                "segments": [
                    "SEG_BB_001", "SEG_BB_003", "SEG_BB_004",
                    "SEG_SP_002", "SEG_DR_002", "SEG_DR_003", "SEG_DR_004",
                ],
                "total_capex_usd": 377_617_000,
                "pct_of_total": "40.2%",
                "rationale": "Phase 2 completes backbone — Abidjan–Takoradi (SEG_BB_001) is largest item.",
            },
            "phase_3": {
                "segments": ["SEG_SP_003", "SEG_BB_005_LEKKI_EXPANSION"],
                "total_capex_usd": 41_287_000,
                "pct_of_total": "4.4%",
                "rationale": "Phase 3 is conditional upside only — corridor base case unaffected if deferred.",
            },
        },

        # ================================================================
        # COST BY COUNTRY
        # ================================================================
        "cost_by_country": {
            "cote_divoire": {
                "capex_usd": 158_000_000,
                "pct_of_total": "16.8%",
                "primary_items": "SEG_BB_001 western half, Abidjan Vridi hub upgrade",
            },
            "ghana": {
                "capex_usd": 342_000_000,
                "pct_of_total": "36.4%",
                "primary_items": "SEG_BB_001 eastern half, SEG_BB_002, SEG_BB_003 western half, Obuasi spur",
            },
            "togo": {
                "capex_usd": 108_000_000,
                "pct_of_total": "11.5%",
                "primary_items": "SEG_BB_003 eastern half, SEG_BB_004 western half, Lomé ring",
            },
            "benin": {
                "capex_usd": 97_000_000,
                "pct_of_total": "10.3%",
                "primary_items": "SEG_BB_004 eastern half, SEG_BB_005 western half, Cotonou hub",
            },
            "nigeria": {
                "capex_usd": 234_000_000,
                "pct_of_total": "24.9%",
                "primary_items": "SEG_BB_005 eastern half, Lekki 400kV hub, Sagamu upgrade",
            },
        },

        # ================================================================
        # COLOCATION SAVINGS BREAKDOWN
        # ================================================================
        "colocation_savings_breakdown": {
            "total_savings_usd": 219_600_000,
            "pct_of_gross_capex": "21.2%",
            "by_category": {
                "access_roads_and_logistics_usd": 98_400_000,
                "land_clearing_and_right_of_way_usd": 72_800_000,
                "security_and_site_establishment_usd": 28_600_000,
                "shared_esia_and_permitting_usd": 19_800_000,
            },
            "highest_saving_segment": {
                "segment": "SEG_BB_004 (Lomé–Cotonou)",
                "overlap_pct": 78.0,
                "saving_usd": 35_600_000,
            },
            "lowest_saving_segment": {
                "segment": "SEG_SP_003 (Lithium Spur)",
                "overlap_pct": 18.0,
                "saving_usd": 900_000,
            },
        },

        "capex_range": "$840M - $1,040M",

        "message": (
            "Detailed cost estimates generated for all 12 corridor segments. "
            "Gross CAPEX before colocation savings: $1,036M. "
            "Colocation savings (21.2%): -$220M — highest savings on Lomé–Cotonou segment (78% overlap). "
            "Net CAPEX after savings and 15% contingency: $939M. "
            "Most expensive single segment: SEG_BB_005 Cotonou–Lagos at $662M "
            "(400kV, double-circuit separate routes, 22km Lagos underground). "
            "Lowest cost intervention: SEG_DR_004 Sagamu substation upgrade at $34M. "
            "Annual OPEX: $24.6M/year (2.6% of net CAPEX — within international benchmark of 1.5–3.0%). "
            "Phase 1 represents 55.4% of total CAPEX — front-loaded to energise "
            "Critical-class anchors and establish revenue base for project financing."
        ),
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