import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import PhasingInput


@tool("generate_phasing_strategy", description=TOOL_DESCRIPTION)
def generate_phasing_strategy_tool(
    payload: PhasingInput, runtime: ToolRuntime
) -> Command:
    """Generates a multi-phase construction plan for the infrastructure."""

    # In a real-world scenario, this tool would:
    # 1. Identify 'Quick Wins' where power can be deployed in 24 months.
    # 2. Sequence construction to match highway 'Lots' (segments).
    # 3. Schedule substation energization to match mining expansion dates.

    response = {
        "corridor_id": "AL_CORRIDOR_POC_001",
        "phasing_philosophy": (
            "Construction is sequenced to maximise early revenue by prioritising "
            "segments with the highest anchor load density and most creditworthy off-takers. "
            "Each phase is aligned with the corresponding Abidjan-Lagos Highway Lot "
            "so that transmission infrastructure is installed using highway construction "
            "access roads — reducing cost and avoiding separate mobilisation. "
            "Critical-class anchors (Dangote Refinery, Obuasi Mine, Tema Port) are "
            "energised in Phase 1 to anchor project financing with guaranteed off-take. "
            "Conditional spurs (Volta agriculture, Lithium) are deferred until "
            "co-financing and licences are confirmed."
        ),

        "highway_schedule_reference": {
            "source": "ALCOMA (Abidjan-Lagos Corridor Management Authority) Master Schedule v2.1",
            "highway_lot_1": {
                "segment": "Abidjan — Takoradi",
                "highway_construction_start": 2027,
                "highway_construction_end": 2030,
                "countries": ["Côte d'Ivoire", "Ghana"],
            },
            "highway_lot_2": {
                "segment": "Takoradi — Accra/Tema",
                "highway_construction_start": 2027,
                "highway_construction_end": 2029,
                "countries": ["Ghana"],
            },
            "highway_lot_3": {
                "segment": "Accra/Tema — Lomé",
                "highway_construction_start": 2028,
                "highway_construction_end": 2031,
                "countries": ["Ghana", "Togo"],
            },
            "highway_lot_4": {
                "segment": "Lomé — Cotonou",
                "highway_construction_start": 2029,
                "highway_construction_end": 2032,
                "countries": ["Togo", "Benin"],
            },
            "highway_lot_5": {
                "segment": "Cotonou — Lagos",
                "highway_construction_start": 2027,
                "highway_construction_end": 2030,
                "countries": ["Benin", "Nigeria"],
            },
        },

        # ================================================================
        # PHASING PLAN — 3 Phases over 8 years
        # ================================================================
        "phasing_plan": [

            {
                "phase": 1,
                "name": "Critical Anchor Connectivity",
                "years": "1-3",
                "calendar_years": "2027-2029",
                "highway_lots_aligned": ["Lot 2 (Takoradi–Tema)", "Lot 5 (Cotonou–Lagos)"],
                "capex_usd": 520_000_000,
                "segments": [
                    {
                        "segment_id": "SEG_BB_002",
                        "name": "Takoradi Hub — Tema/Accra Hub (Ghana Backbone Upgrade)",
                        "rationale": (
                            "Highest revenue density on corridor — Tema cluster alone "
                            "represents 200 MW current demand including Tema Port (Critical). "
                            "Existing 161kV towers (70% reusable) cut CAPEX by $45M. "
                            "GRIDCo Ghana already has this upgrade in national plan — "
                            "fastest permits and lowest risk segment on corridor. "
                            "Energisation target: Q4 2028."
                        ),
                        "anchor_loads_energised": [
                            "AL_ANC_008",  # Tema Port MPS — Critical
                            "AL_ANC_009",  # Tema Free Zone — Critical
                            "AL_ANC_016",  # Nzema Solar feed-in
                        ],
                        "energisation_year": 2028,
                        "revenue_at_energisation_usd_per_year": 28_000_000,
                    },
                    {
                        "segment_id": "SEG_BB_005",
                        "name": "Cotonou Hub — Lagos/Lekki Hub (Benin–Nigeria Backbone)",
                        "rationale": (
                            "Dangote Refinery (1,000 MW) is the single largest anchor load "
                            "on the corridor — corporate guarantee from Dangote Industries "
                            "anchors project financing for the entire corridor. "
                            "Lekki FTZ (Phase 1B) begins production 2028 — power must be "
                            "available at commissioning. Co-location with Lot 5 highway "
                            "construction saves $38M in access road costs. "
                            "Energisation target: Q2 2029."
                        ),
                        "anchor_loads_energised": [
                            "AL_ANC_027",  # Dangote Refinery — Critical, 1,000 MW
                            "AL_ANC_028",  # Lekki FTZ Phase 1 — 150 MW
                            "AL_ANC_029",  # Lekki Deep Sea Port
                            "AL_ANC_030",  # MainOne Data Center — Critical
                        ],
                        "energisation_year": 2029,
                        "revenue_at_energisation_usd_per_year": 65_000_000,
                    },
                    {
                        "segment_id": "SEG_SP_001",
                        "name": "Kumasi Hub — Obuasi Gold Mine Dedicated Spur",
                        "rationale": (
                            "AngloGold Ashanti corporate guarantee (investment-grade credit) "
                            "makes this spur fully bankable on a standalone basis. "
                            "Mine is at 85% production capacity — grid connection unlocks "
                            "remaining 15% ($45M/year incremental revenue for AngloGold). "
                            "Mine pays $0.09/kWh vs $0.24/kWh diesel — "
                            "immediate $12M/year saving drives fast PPA signature. "
                            "Energisation target: Q1 2029."
                        ),
                        "anchor_loads_energised": [
                            "AL_ANC_012",  # Obuasi Gold Mine — Critical
                        ],
                        "energisation_year": 2029,
                        "revenue_at_energisation_usd_per_year": 9_500_000,
                    },
                ],
                "substations_commissioned": [
                    "HUB_TEMA_INDUSTRIAL",
                    "HUB_LEKKI_400KV (Phase 1A — 500 MW)",
                    "SUB_KUMASI_330KV",
                    "SUB_OBUASI_MINE",
                    "SUB_LOME_INDUSTRIAL_RING",
                ],
                "phase_1_total_revenue_year_3_usd": 102_500_000,
                "phase_1_anchor_mw_connected": 1_480,
                "key_milestones": [
                    {
                        "milestone": "Financial Close",
                        "target_date": "Q2 2027",
                        "dependencies": [
                            "Dangote corporate guarantee signed",
                            "AngloGold Ashanti PPA signed",
                            "AfDB and IFC term sheets executed",
                        ],
                    },
                    {
                        "milestone": "Construction Start — SEG_BB_002 and SEG_BB_005",
                        "target_date": "Q3 2027",
                        "dependencies": [
                            "Highway Lot 2 and Lot 5 construction access roads open",
                            "NERC Nigeria cross-border approval received",
                            "GRIDCo Ghana joint development agreement signed",
                        ],
                    },
                    {
                        "milestone": "Tema Industrial Hub energisation",
                        "target_date": "Q4 2028",
                        "dependencies": [
                            "SEG_BB_002 stringing complete",
                            "Tema Industrial 330kV bay commissioning",
                            "GRIDCo protection relay settings agreed",
                        ],
                    },
                    {
                        "milestone": "Lekki 400kV Hub Phase 1A energisation",
                        "target_date": "Q2 2029",
                        "dependencies": [
                            "SEG_BB_005 underground XLPE section complete (22km Lagos Island)",
                            "Dangote Refinery 330kV receiving substation ready",
                            "NERC Nigeria commissioning inspection passed",
                        ],
                    },
                ],
                "risks": [
                    {
                        "risk": "Lagos underground XLPE section (22km) — longest and most complex construction item",
                        "probability": "Medium",
                        "impact": "6-month delay to Lekki hub energisation",
                        "mitigation": "Begin underground section 6 months ahead of overhead stringing; dual contractor mobilisation",
                    },
                    {
                        "risk": "NERC Nigeria cross-border approval — regulatory timeline uncertainty",
                        "probability": "Medium",
                        "impact": "Delays financial close",
                        "mitigation": "Engage NERC at pre-application stage in Q1 2026 ahead of construction start",
                    },
                ],
            },

            {
                "phase": 2,
                "name": "Coastal Backbone Completion",
                "years": "3-6",
                "calendar_years": "2030-2032",
                "highway_lots_aligned": ["Lot 1 (Abidjan–Takoradi)", "Lot 3 (Tema–Lomé)", "Lot 4 (Lomé–Cotonou)"],
                "capex_usd": 410_000_000,
                "segments": [
                    {
                        "segment_id": "SEG_BB_001",
                        "name": "Abidjan Hub — Takoradi Hub (Coastal Backbone)",
                        "rationale": (
                            "Longest segment at 382km — deferred to Phase 2 to allow "
                            "Côte d'Ivoire / Ghana border crossing approvals to mature. "
                            "Joint ministerial approval process begins in Phase 1 (2027) "
                            "targeting signature by 2029. "
                            "Lot 1 highway construction access roads open by 2028 — "
                            "stringing can follow highway works westward. "
                            "Abidjan anchors (Azito, CIPREL) have existing grid supply "
                            "and do not require Phase 1 urgency. "
                            "Energisation target: Q3 2031."
                        ),
                        "anchor_loads_energised": [
                            "AL_ANC_003",  # Azito Thermal Plant
                            "AL_ANC_004",  # CIPREL Power Plant
                            "AL_ANC_005",  # Port of Abidjan Industrial Zone
                            "AL_ANC_015",  # Takoradi Port
                        ],
                        "energisation_year": 2031,
                        "revenue_at_energisation_usd_per_year": 22_000_000,
                    },
                    {
                        "segment_id": "SEG_BB_003",
                        "name": "Tema Hub — Lomé Hub (Ghana–Togo Coastal Backbone)",
                        "rationale": (
                            "Follows Lot 3 highway construction east from Tema. "
                            "Aflao/Lomé border urban section (14km underground XLPE) "
                            "is the critical path item — begin design in Phase 1. "
                            "Togo ARSE regulatory approval process starts 2028 "
                            "to be ready for Phase 2 construction. "
                            "Lomé hub (HUB_LOME_TOKOIN) is already commissioned "
                            "in Phase 1 — SEG_BB_003 simply connects to it. "
                            "Energisation target: Q2 2031."
                        ),
                        "anchor_loads_energised": [
                            "AL_ANC_017",  # Port of Lomé
                            "AL_ANC_019",  # Lomé Cement Plant
                            "AL_ANC_020",  # Lomé Free Zone
                        ],
                        "energisation_year": 2031,
                        "revenue_at_energisation_usd_per_year": 14_000_000,
                    },
                    {
                        "segment_id": "SEG_BB_004",
                        "name": "Lomé Hub — Cotonou Hub (Togo–Benin Coastal Backbone)",
                        "rationale": (
                            "Closes the last coastal backbone gap between Lomé and Cotonou. "
                            "Porto-Novo urban underground section (6km) begins construction "
                            "in 2030 ahead of overhead stringing. "
                            "Maria Gleta hub (HUB_COTONOU_MARIA_GLETA) commissioned "
                            "simultaneously — serves as Phase 2 western terminus. "
                            "Benin import dependency (85%) makes this segment transformative "
                            "for national energy security. "
                            "Energisation target: Q4 2031."
                        ),
                        "anchor_loads_energised": [
                            "AL_ANC_022",  # Port of Cotonou
                            "AL_ANC_023",  # Zone Industrielle Cotonou
                        ],
                        "energisation_year": 2031,
                        "revenue_at_energisation_usd_per_year": 11_000_000,
                    },
                    {
                        "segment_id": "SEG_SP_002",
                        "name": "Akuse Hub — Volta Agricultural Belt Spur (Conditional)",
                        "rationale": (
                            "CONDITIONAL on AfDB SAPZ co-financing approval (target: 2028) "
                            "and COCOBOD aggregation PPA signature. "
                            "If conditions met by end of Phase 1, construction begins "
                            "in Year 4 (2030) — aligns with Volta irrigation expansion plan. "
                            "Low highway co-location (22%) — independent construction schedule. "
                            "Energisation target: Q2 2032 (if conditions met)."
                        ),
                        "anchor_loads_energised": [
                            "AL_ANC_014",  # Weta Rice Farm / Volta Agricultural Belt
                        ],
                        "energisation_year": 2032,
                        "revenue_at_energisation_usd_per_year": 1_800_000,
                        "conditional": True,
                        "conditions_required": [
                            "AfDB SAPZ co-financing approved",
                            "Weta operator identity confirmed",
                            "COCOBOD aggregation PPA signed",
                        ],
                    },
                    {
                        "segment_id": "SEG_DR_002",
                        "name": "Zone Industrielle Cotonou Dedicated 33kV Feeder",
                        "rationale": (
                            "Follows Maria Gleta hub commissioning — "
                            "8km XLPE feeder installed once hub is energised. "
                            "STATCOM equipment ordered in Phase 1 (long lead item). "
                            "Energisation target: Q1 2032."
                        ),
                        "anchor_loads_energised": ["AL_ANC_023"],
                        "energisation_year": 2032,
                        "revenue_at_energisation_usd_per_year": 4_200_000,
                    },
                    {
                        "segment_id": "SEG_DR_003",
                        "name": "Abidjan Vridi 225/11kV Industrial Substation Upgrade",
                        "rationale": (
                            "Follows Abidjan hub (HUB_ABIDJAN_VRIDI) commissioning. "
                            "Separates industrial supply from CIE residential distribution. "
                            "Energisation target: Q4 2031."
                        ),
                        "anchor_loads_energised": [
                            "AL_ANC_003", "AL_ANC_004", "AL_ANC_005",
                        ],
                        "energisation_year": 2031,
                        "revenue_at_energisation_usd_per_year": 8_500_000,
                    },
                    {
                        "segment_id": "SEG_DR_004",
                        "name": "Sagamu Interchange 132kV Substation Upgrade",
                        "rationale": (
                            "Lowest cost item on corridor ($28M) — "
                            "transformer replacement only, no new line construction. "
                            "Scheduled for Phase 2 to align with Lekki FTZ Phase 1B "
                            "buildout increasing load on TCN 132kV ring. "
                            "Energisation target: Q3 2031."
                        ),
                        "anchor_loads_energised": ["AL_ANC_032"],
                        "energisation_year": 2031,
                        "revenue_at_energisation_usd_per_year": 3_600_000,
                    },
                ],
                "substations_commissioned": [
                    "HUB_ABIDJAN_VRIDI",
                    "HUB_TAKORADI_ABOADZE",
                    "HUB_LOME_TOKOIN",
                    "HUB_COTONOU_MARIA_GLETA",
                    "HUB_LEKKI_400KV (Phase 1B — 2,500 MW)",
                    "SUB_AKUSE_161KV (conditional)",
                    "SUB_WETA_ZONE (conditional)",
                    "SUB_ABIDJAN_VRIDI_UPGRADE",
                    "SUB_COTONOU_INDUSTRIAL",
                    "SUB_SAGAMU_132KV_UPGRADE",
                ],
                "phase_2_total_revenue_year_6_usd": 65_100_000,
                "phase_2_anchor_mw_connected": 680,
                "key_milestones": [
                    {
                        "milestone": "Côte d'Ivoire / Ghana border crossing approval",
                        "target_date": "Q2 2029",
                        "dependencies": [
                            "Joint ministerial working group established (initiated Phase 1)",
                            "WAPP cross-border interconnection agreement signed",
                            "Elubo border post ESIA approved",
                        ],
                    },
                    {
                        "milestone": "SEG_BB_001 Abidjan–Takoradi stringing complete",
                        "target_date": "Q1 2031",
                        "dependencies": [
                            "Ankasa Reserve 8km deviation ESIA approved",
                            "Half Assini coastal erosion tower foundations complete",
                            "Lot 1 highway access roads open from Abidjan end",
                        ],
                    },
                    {
                        "milestone": "Full coastal backbone energised (Abidjan to Lagos)",
                        "target_date": "Q4 2031",
                        "dependencies": [
                            "All 4 backbone segments commissioned",
                            "WAPP operational testing complete",
                            "5-country SCADA integration live",
                        ],
                    },
                    {
                        "milestone": "AfDB SAPZ Volta co-financing decision",
                        "target_date": "Q4 2028",
                        "dependencies": [
                            "Feasibility study submitted to AfDB",
                            "COCOBOD PPA term sheet agreed",
                            "Ghana Ministry of Food and Agriculture endorsement",
                        ],
                    },
                ],
                "risks": [
                    {
                        "risk": "SEG_BB_001 border crossing approval delay — two-country ministerial process",
                        "probability": "Medium-High",
                        "impact": "Up to 12-month delay on Abidjan hub energisation",
                        "mitigation": "Engage both energy ministries in Phase 1 (2027); ECOWAS facilitation requested",
                    },
                    {
                        "risk": "AfDB SAPZ co-financing not approved — Volta spur becomes stranded",
                        "probability": "Low-Medium",
                        "impact": "SEG_SP_002 deferred to Phase 3 or cancelled",
                        "mitigation": "Spur is conditional by design; corridor economics unaffected if cancelled",
                    },
                ],
            },

            {
                "phase": 3,
                "name": "Optimisation and Conditional Extensions",
                "years": "6-8",
                "calendar_years": "2033-2035",
                "capex_usd": 95_000_000,
                "segments": [
                    {
                        "segment_id": "SEG_SP_003",
                        "name": "Mampong Hub — Lithium Site Dedicated Spur (Conditional)",
                        "rationale": (
                            "CONDITIONAL on Ghana Minerals Commission licence approval "
                            "and operator identity confirmation. "
                            "Lithium demand for EV batteries makes this a high-upside "
                            "opportunity ($140 MW by Year 20) but timing is uncertain. "
                            "Phase 3 construction window aligns with expected "
                            "mine development timeline post-licence. "
                            "Energisation target: Q3 2035 (if conditions met)."
                        ),
                        "anchor_loads_energised": [
                            "AL_ANC_035",  # Lithium Site
                        ],
                        "energisation_year": 2035,
                        "revenue_at_energisation_usd_per_year": 1_200_000,
                        "conditional": True,
                        "conditions_required": [
                            "Ghana Minerals Commission licence granted",
                            "Operator identity confirmed",
                            "Operator corporate guarantee secured for spur financing",
                        ],
                    },
                    {
                        "segment_id": "SEG_BB_005_UPGRADE",
                        "name": "Lekki 400kV Hub — Phase 1B to Full Capacity Upgrade",
                        "rationale": (
                            "Lekki FTZ Phase 2 buildout (Year 5-8) increases load from "
                            "150 MW to 800 MW — additional transformer bays and feeders "
                            "required at Lekki hub. "
                            "Phase 1B design already accommodates this expansion — "
                            "incremental CAPEX only ($45M for additional bays). "
                            "Dangote Refinery Phase 2 (petrochemical expansion) adds "
                            "200 MW — dedicated feeder upgrade required. "
                            "Energisation target: Q2 2034."
                        ),
                        "anchor_loads_energised": [
                            "AL_ANC_028",  # Lekki FTZ Phase 2 expansion
                        ],
                        "energisation_year": 2034,
                        "revenue_at_energisation_usd_per_year": 35_000_000,
                    },
                    {
                        "segment_id": "DR_LOOP_EXPANSION",
                        "name": "Corridor Distribution Loop Expansion — New Industrial Tenants",
                        "rationale": (
                            "By Year 6, corridor economic zones will have attracted "
                            "new industrial tenants not yet identified. "
                            "Phase 3 budget allocation for opportunistic distribution "
                            "connections to materialising demand. "
                            "Specific segments defined during Phase 2 based on actual "
                            "zone tenant contracts signed."
                        ),
                        "anchor_loads_energised": ["TBD — new industrial tenants"],
                        "energisation_year": 2035,
                        "revenue_at_energisation_usd_per_year": 8_000_000,
                        "conditional": True,
                    },
                ],
                "substations_commissioned": [
                    "SUB_MAMPONG_161KV (conditional)",
                    "HUB_LEKKI_400KV (Phase 1B full buildout)",
                ],
                "phase_3_total_revenue_year_8_usd": 44_200_000,
                "phase_3_anchor_mw_connected": 340,
                "key_milestones": [
                    {
                        "milestone": "Ghana lithium mining licence — go/no-go decision for SEG_SP_003",
                        "target_date": "Q2 2032",
                        "dependencies": [
                            "Ghana Minerals Commission review complete",
                            "Operator due diligence concluded",
                        ],
                    },
                    {
                        "milestone": "Lekki FTZ Phase 2 buildout demand confirmation",
                        "target_date": "Q1 2033",
                        "dependencies": [
                            "Lekki FTZ authority tenant contracts signed (Year 5 target)",
                            "Demand profile update from Phase 2 monitoring data",
                        ],
                    },
                    {
                        "milestone": "Full corridor operational — all 15 substations live",
                        "target_date": "Q4 2035",
                        "dependencies": [
                            "All conditional spurs resolved (go or formally cancelled)",
                            "WAPP AfSEM integration complete",
                            "5-country corridor operations centre operational",
                        ],
                    },
                ],
                "risks": [
                    {
                        "risk": "Lithium site licence delayed beyond 2032 — spur becomes unviable",
                        "probability": "Medium",
                        "impact": "SEG_SP_003 cancelled — $95M Phase 3 CAPEX reduced to $50M",
                        "mitigation": "Corridor economics fully funded by Phases 1 and 2; Phase 3 is upside only",
                    },
                ],
            },
        ],

        # ================================================================
        # CORRIDOR-LEVEL SUMMARY
        # ================================================================
        "corridor_summary": {
            "total_phases": 3,
            "total_construction_years": 8,
            "calendar_span": "2027-2035",
            "total_capex_usd": 1_025_000_000,

            "capex_by_phase": {
                "phase_1_usd": 520_000_000,
                "phase_2_usd": 410_000_000,
                "phase_3_usd": 95_000_000,
            },

            "revenue_ramp": {
                "year_1_usd": 0,
                "year_2_usd": 0,
                "year_3_usd": 102_500_000,   # Phase 1 anchors energised
                "year_4_usd": 118_000_000,
                "year_5_usd": 134_000_000,
                "year_6_usd": 167_600_000,   # Phase 2 full backbone online
                "year_8_usd": 211_800_000,   # Phase 3 expansions
                "year_10_usd": 245_000_000,  # Full anchor load growth
            },

            "anchor_mw_connected_by_phase": {
                "after_phase_1": 1_480,
                "after_phase_2": 2_160,
                "after_phase_3": 2_500,
            },

            "alignment_summary": {
                "highway_lot_1_abidjan_takoradi": "Phase 2 (SEG_BB_001)",
                "highway_lot_2_takoradi_tema": "Phase 1 (SEG_BB_002)",
                "highway_lot_3_tema_lome": "Phase 2 (SEG_BB_003)",
                "highway_lot_4_lome_cotonou": "Phase 2 (SEG_BB_004)",
                "highway_lot_5_cotonou_lagos": "Phase 1 (SEG_BB_005)",
                "note": (
                    "Phase 1 prioritises Lots 2 and 5 — both have highest anchor "
                    "load density and earliest highway construction start. "
                    "Lots 1, 3, and 4 follow in Phase 2 aligned with highway works."
                ),
            },

            "conditional_segments": {
                "count": 2,
                "segments": ["SEG_SP_002 (Volta agri)", "SEG_SP_003 (Lithium)"],
                "combined_capex_if_both_proceed_usd": 84_000_000,
                "note": (
                    "Both conditional segments are upside — corridor base case "
                    "financials do not depend on either proceeding."
                ),
            },
        },

        "message": (
            "3-Phase strategy generated, aligned with Abidjan-Lagos Highway Lots 1–5. "
            "Phase 1 (2027-2029, $520M) connects 1,480 MW of Critical-class anchors "
            "including Dangote Refinery, Obuasi Gold Mine, and Tema Port — "
            "generating $102.5M/year revenue by Year 3 to service project debt. "
            "Phase 2 (2030-2032, $410M) completes the full coastal backbone across all 5 countries. "
            "Phase 3 (2033-2035, $95M) covers conditional extensions and capacity upgrades. "
            "2 conditional spurs (Volta agriculture, Lithium) deferred pending co-financing "
            "and licence approvals — corridor base case unaffected if either is cancelled."
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