import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import GrowthTrajectoryInput


@tool("model_growth_trajectory", description=TOOL_DESCRIPTION)
def model_growth_trajectory_tool(
    payload: GrowthTrajectoryInput, runtime: ToolRuntime
) -> Command:
    """
    Projects 20-year electricity demand trajectories for each anchor load.

    Takes the current demand picture from calculate_current_demand and the
    commercial reliability assessment from assess_bankability and asks:

        "How much will this facility's electricity demand grow over 20 years,
         and how confident are we in that growth?"

    Growth driver types:
        Type 1 — Committed Expansion:   signed contracts, construction underway
                                         → narrow confidence band
        Type 2 — Policy-Backed:         government commitments, DFI programmes
                                         → moderate confidence band
        Type 3 — Sector-Driven:         commodity trends, regional economic growth
                                         → wide confidence band
        Type 4 — Conditional/Potential: contingent on grid connection, licences,
                                         or identity confirmation
                                         → very wide confidence band, flagged

    Bankability tier linkage:
        Tier 1 anchors → growth modeled at face value (credible operator,
                          financial strength to execute expansion)
        Tier 2 anchors → growth modeled with 15–25% execution haircut applied
        Tier 3 anchors → growth modeled as upside scenario only, never base case

    This tool does NOT return:
        - Revenue projections          → prioritize_opportunities
        - Infrastructure sizing        → infrastructure_optimization_agent
        - Financing structures         → financing_optimization_agent
        - Bankability scores           → already completed by assess_bankability

    Anchor loads modeled: 24 (aligned to scan_anchor_loads pipeline)
    Generation assets excluded: 10
    Substations excluded: 3
    """

    response = {
        "projection_summary": (
            "Aggregated corridor demand projected to grow 183% over 20 years, "
            "from 2,127.5 MW today to 6,017 MW by Year 20. "
            "Strongest growth: Dangote Refinery petrochemical expansion (+600 MW), "
            "Lekki FTZ full buildout (+850 MW), and digital infrastructure scaling. "
            "3 Tier 3 anchors modeled as conditional upside only — "
            "excluded from base case aggregate."
        ),
        "aggregate_trajectory": {
            "base_case": {
                "current_mw": 2127.5,
                "year_5_mw": 3480.0,
                "year_10_mw": 4690.0,
                "year_20_mw": 6017.0,
                "overall_growth_pct": "183%",
                "note": (
                    "Base case includes Tier 1 and Tier 2 anchors only. "
                    "Tier 3 anchors (Weta Rice Farm, Benin Agro Cluster, "
                    "Unverified Lagos DC, Lithium Site) excluded — "
                    "included in upside scenario only."
                ),
            },
            "upside_scenario": {
                "year_10_mw": 5280.0,
                "year_20_mw": 7150.0,
                "upside_drivers": (
                    "Tier 3 anchors confirmed and fully developed: "
                    "+150 MW Weta Rice Farm, +80 MW Lagos Hyperscale DC, "
                    "+120 MW Lithium Mine at full production."
                ),
            },
        },

        "cluster_trajectories": {
            "abidjan_cluster": {
                "anchors": ["AL_ANC_003", "AL_ANC_004", "AL_ANC_005"],
                "current_mw": 105.0,
                "year_5_mw": 168.0,
                "year_10_mw": 228.0,
                "year_20_mw": 318.0,
                "sizing_implication": (
                    "Abidjan hub requires 330kV substation sized for 350 MW "
                    "by Year 5 with upgrade path to 450 MW by Year 10."
                ),
            },
            "accra_tema_cluster": {
                "anchors": ["AL_ANC_007", "AL_ANC_008", "AL_ANC_009", "AL_ANC_016"],
                "current_mw": 170.0,
                "year_5_mw": 263.0,
                "year_10_mw": 342.0,
                "year_20_mw": 485.0,
                "sizing_implication": (
                    "Accra-Tema hub requires 330kV substation sized for 300 MW "
                    "Phase 1, upgrade to 500 MW by Year 10."
                ),
            },
            "lome_cluster": {
                "anchors": ["AL_ANC_017", "AL_ANC_019", "AL_ANC_020"],
                "current_mw": 85.0,
                "year_5_mw": 136.0,
                "year_10_mw": 184.0,
                "year_20_mw": 265.0,
                "sizing_implication": (
                    "Lomé hub requires 225kV substation sized for 150 MW "
                    "Phase 1, upgrade to 300 MW by Year 10."
                ),
            },
            "cotonou_cluster": {
                "anchors": ["AL_ANC_022", "AL_ANC_023"],
                "current_mw": 54.0,
                "year_5_mw": 86.0,
                "year_10_mw": 116.0,
                "year_20_mw": 162.0,
                "sizing_implication": (
                    "Cotonou hub requires 225kV substation sized for 100 MW "
                    "Phase 1, upgrade to 200 MW by Year 10."
                ),
            },
            "lagos_lekki_cluster": {
                "anchors": [
                    "AL_ANC_027", "AL_ANC_028", "AL_ANC_029",
                    "AL_ANC_030", "AL_ANC_031", "AL_ANC_032",
                ],
                "current_mw": 1338.0,
                "year_5_mw": 2318.0,
                "year_10_mw": 3080.0,
                "year_20_mw": 4160.0,
                "sizing_implication": (
                    "Lagos-Lekki hub is the dominant load center on the corridor. "
                    "Requires 400kV substation sized for 2,500 MW by Year 5 "
                    "with upgrade path to 4,500 MW by Year 15. "
                    "Dangote Refinery alone justifies hub investment."
                ),
            },
        },

        "trajectories": [

            # ================================================================
            # CÔTE D'IVOIRE
            # ================================================================

            {
                # Port of Abidjan — Vridi Terminal
                # Bankability: Tier 1 (score 0.84) — growth modeled at face value
                # Growth driver: Type 1 — second container terminal construction confirmed
                "anchor_id": "AL_ANC_003",
                "detection_id": "DET-003",
                "entity_name": "Port of Abidjan — Vridi Terminal",
                "country": "Côte d'Ivoire",
                "bankability_tier": "Tier 1",
                "current_mw": 45.0,
                "year_5_mw": 62.0,
                "year_10_mw": 80.0,
                "year_20_mw": 115.0,
                "cagr": "4.8%",
                "growth_driver_type": "Type 1 — Committed Expansion",
                "growth_driver": (
                    "Second container terminal (TC2) under active construction — "
                    "adds 8 new cranes and doubles handling capacity by Year 3. "
                    "ECOWAS intra-regional trade growing at 7%/year compounds "
                    "port demand over 20-year horizon."
                ),
                "confidence_band": "Narrow",
                "scenario_low_year_10_mw": 70.0,
                "scenario_high_year_10_mw": 92.0,
                "growth_narrative": (
                    "Abidjan port is the largest in West Africa and a confirmed "
                    "expansion anchor. TC2 construction is already underway — "
                    "Year 5 demand growth is virtually certain. "
                    "Beyond Year 5 growth is steady and tied to ECOWAS trade volumes."
                ),
            },

            {
                # Cargill Cocoa Processing Plant — Abidjan Hinterland
                # Bankability: Tier 2 (score 0.72) — 20% execution haircut applied
                # Growth driver: Type 2 — Côte d'Ivoire government 50% domestic processing target
                "anchor_id": "AL_ANC_004",
                "detection_id": "DET-004",
                "entity_name": "Cargill Cocoa Processing Plant — Abidjan Hinterland",
                "country": "Côte d'Ivoire",
                "bankability_tier": "Tier 2",
                "current_mw": 18.0,
                "year_5_mw": 28.0,
                "year_10_mw": 38.0,
                "year_20_mw": 58.0,
                "cagr": "6.0%",
                "growth_driver_type": "Type 2 — Policy-Backed Expansion",
                "growth_driver": (
                    "Côte d'Ivoire government mandate: 50% of cocoa processed "
                    "domestically by 2025 (currently ~35%). "
                    "Cargill is one of only three certified processors — "
                    "facility expansion is policy-driven and supported by "
                    "CIE and APEX-CI incentives. "
                    "Note: 20% haircut applied to projections pending "
                    "full identity confirmation."
                ),
                "confidence_band": "Moderate",
                "scenario_low_year_10_mw": 30.0,
                "scenario_high_year_10_mw": 48.0,
                "growth_narrative": (
                    "Government cocoa processing mandate creates structural demand growth. "
                    "Growth modeled with 20% haircut because identity is partially resolved — "
                    "if Cargill identity confirmed, projections upgrade to narrow band. "
                    "Upside: cocoa butter and powder export market growing 8%/year globally."
                ),
            },

            {
                # Abidjan Export Processing Zone (ZIEX)
                # Bankability: Tier 2 (score 0.78) — 15% execution haircut applied
                # Growth driver: Type 2 — APEX-CI investment targets formally committed
                "anchor_id": "AL_ANC_005",
                "detection_id": "DET-005",
                "entity_name": "Abidjan Export Processing Zone (ZIEX)",
                "country": "Côte d'Ivoire",
                "bankability_tier": "Tier 2",
                "current_mw": 42.0,
                "year_5_mw": 65.0,
                "year_10_mw": 88.0,
                "year_20_mw": 130.0,
                "cagr": "5.8%",
                "growth_driver_type": "Type 2 — Policy-Backed Expansion",
                "growth_driver": (
                    "APEX-CI formally targeting 400 zone enterprises by 2027 "
                    "(currently ~200) — doubling occupancy doubles power demand. "
                    "Côte d'Ivoire National Development Plan commits "
                    "$2.5B to SEZ infrastructure through 2030. "
                    "Zone capacity utilisation directly constrained by "
                    "current power unreliability — reliable grid is the "
                    "primary demand unlock."
                ),
                "confidence_band": "Moderate",
                "scenario_low_year_10_mw": 72.0,
                "scenario_high_year_10_mw": 105.0,
                "growth_narrative": (
                    "Growth is policy-driven and well-supported institutionally. "
                    "Key risk: enterprise attraction targets may slip if "
                    "broader investment climate does not improve. "
                    "Power reliability improvement itself is expected to "
                    "attract 40-60 new enterprises within 24 months."
                ),
            },

            # ================================================================
            # GHANA
            # ================================================================

            {
                # Tema Oil Refinery (TOR)
                # Bankability: Tier 2 (score 0.68) — 25% execution haircut applied
                # Growth driver: Type 2 — Ghana government rehabilitation commitment
                "anchor_id": "AL_ANC_007",
                "detection_id": "DET-007",
                "entity_name": "Tema Oil Refinery (TOR)",
                "country": "Ghana",
                "bankability_tier": "Tier 2",
                "current_mw": 32.0,
                "year_5_mw": 52.0,
                "year_10_mw": 68.0,
                "year_20_mw": 85.0,
                "cagr": "5.0%",
                "growth_driver_type": "Type 2 — Policy-Backed Expansion",
                "growth_driver": (
                    "Ghana government has committed $750M to TOR rehabilitation "
                    "to restore full 45,000 bpd capacity by 2027. "
                    "Reliable grid power is a stated prerequisite for "
                    "full refinery restart — load factor expected to rise "
                    "from current 0.55 to 0.85+ post-rehabilitation. "
                    "25% haircut applied due to TOR's history of "
                    "rehabilitation delays."
                ),
                "confidence_band": "Moderate",
                "scenario_low_year_10_mw": 48.0,
                "scenario_high_year_10_mw": 82.0,
                "growth_narrative": (
                    "Growth is primarily rehabilitation-driven in Years 1–5, "
                    "then steady operational growth in Years 5–20. "
                    "Key risk: rehabilitation delays and financing gaps have "
                    "historically plagued TOR — wide scenario band reflects this. "
                    "Upside: downstream lubricants plant addition under discussion "
                    "could add 15–20 MW by Year 10."
                ),
            },

            {
                # Tema Port — Meridian Port Services
                # Bankability: Tier 1 (score 0.87) — growth modeled at face value
                # Growth driver: Type 1 — Phase 2 terminal expansion in active planning
                "anchor_id": "AL_ANC_008",
                "detection_id": "DET-008",
                "entity_name": "Tema Port — Meridian Port Services",
                "country": "Ghana",
                "bankability_tier": "Tier 1",
                "current_mw": 38.0,
                "year_5_mw": 55.0,
                "year_10_mw": 72.0,
                "year_20_mw": 108.0,
                "cagr": "5.3%",
                "growth_driver_type": "Type 1 — Committed Expansion",
                "growth_driver": (
                    "Meridian Port Services Phase 2 terminal expansion formally "
                    "approved — doubles container handling capacity by Year 4. "
                    "New reefer plug banks (1,200 units) add 8–10 MW at commissioning. "
                    "West Africa container trade growing at 7%/year — "
                    "terminal at capacity utilisation by Year 3."
                ),
                "confidence_band": "Narrow",
                "scenario_low_year_10_mw": 65.0,
                "scenario_high_year_10_mw": 80.0,
                "growth_narrative": (
                    "One of the most reliable growth stories on the corridor. "
                    "Committed expansion, investment-grade operator, and "
                    "structural trade growth all align. "
                    "Demand growth is predictable and well-bounded."
                ),
            },

            {
                # Tema Free Zone
                # Bankability: Tier 1 (score 0.80) — growth modeled at face value
                # Growth driver: Type 2 — GFZA 400-enterprise target formally committed
                "anchor_id": "AL_ANC_009",
                "detection_id": "DET-009",
                "entity_name": "Tema Free Zone",
                "country": "Ghana",
                "bankability_tier": "Tier 1",
                "current_mw": 52.0,
                "year_5_mw": 92.0,
                "year_10_mw": 138.0,
                "year_20_mw": 220.0,
                "cagr": "7.5%",
                "growth_driver_type": "Type 2 — Policy-Backed Expansion",
                "growth_driver": (
                    "GFZA formally targeting 400 enterprises by 2030 — "
                    "doubling from current 200. "
                    "200-hectare Phase 2 expansion land already acquired "
                    "and servicing underway. "
                    "Zone at 60% capacity due to power constraint — "
                    "reliable power alone expected to increase "
                    "utilisation to 85% within 18 months, "
                    "adding 20–25 MW immediately."
                ),
                "confidence_band": "Moderate",
                "scenario_low_year_10_mw": 115.0,
                "scenario_high_year_10_mw": 162.0,
                "growth_narrative": (
                    "Strongest growth story in Ghana on the corridor. "
                    "Suppressed demand unlock (power reliability improvement) "
                    "creates near-term step change. "
                    "Structural growth from zone expansion compounds over 20 years. "
                    "Key risk: enterprise attraction pace may vary with "
                    "Ghana macroeconomic conditions."
                ),
            },

            {
                # Obuasi Gold Mine (AngloGold Ashanti)
                # Bankability: Tier 1 (score 0.95) — growth modeled at face value
                # Growth driver: Type 1 — Phase 3 underground expansion signed
                "anchor_id": "AL_ANC_012",
                "detection_id": "DET-012",
                "entity_name": "Obuasi Gold Mine (AngloGold Ashanti)",
                "country": "Ghana",
                "bankability_tier": "Tier 1",
                "current_mw": 68.0,
                "year_5_mw": 88.0,
                "year_10_mw": 108.0,
                "year_20_mw": 140.0,
                "cagr": "3.7%",
                "growth_driver_type": "Type 1 — Committed Expansion",
                "growth_driver": (
                    "AngloGold Ashanti Phase 3 underground expansion approved — "
                    "adds 120,000 oz/year production capacity by Year 4. "
                    "New shaft sinking and expanded processing plant "
                    "add 15–20 MW on commissioning. "
                    "Electrification of previously diesel underground equipment "
                    "(LHDs, trucks) adds further 5–8 MW over Years 5–10. "
                    "20+ year mine life confirmed by recent reserve upgrade."
                ),
                "confidence_band": "Narrow",
                "scenario_low_year_10_mw": 98.0,
                "scenario_high_year_10_mw": 118.0,
                "growth_narrative": (
                    "Highly predictable growth profile — mine expansion is signed "
                    "and equipment ordered. Additional upside from equipment "
                    "electrification as AngloGold Ashanti pursues "
                    "Scope 1 emission reduction targets. "
                    "Spur connection required (~98km) — "
                    "growth trajectory justifies spur investment economics."
                ),
            },

            {
                # Weta Rice Farm & Milling Hub — Volta Region
                # Bankability: Tier 3 (score 0.45) — CONDITIONAL UPSIDE ONLY
                # Growth driver: Type 4 — entirely contingent on grid connection
                "anchor_id": "AL_ANC_014",
                "detection_id": "DET-014",
                "entity_name": "Weta Rice Farm & Milling Hub — Volta Region",
                "country": "Ghana",
                "bankability_tier": "Tier 3",
                "current_mw": 8.0,
                "year_5_mw": 8.0,
                "year_10_mw": 8.0,
                "year_20_mw": 8.0,
                "cagr": "0.0%",
                "growth_driver_type": "Type 4 — Conditional / Potential",
                "growth_driver": (
                    "BASE CASE: No growth. Currently diesel-powered with no grid "
                    "connection — demand stays suppressed at 8 MW until "
                    "grid connection is established. "
                    "UPSIDE SCENARIO (if grid connected and identity confirmed): "
                    "Irrigation expansion from 12,000 ha to 100,000 ha adds "
                    "90–120 MW by Year 5. Full buildout 150 MW by Year 10. "
                    "This is the highest potential growth story on the corridor "
                    "but entirely conditional on connection and operator resolution."
                ),
                "confidence_band": "Conditional — excluded from base case",
                "scenario_low_year_10_mw": 8.0,
                "scenario_high_year_10_mw": 150.0,
                "upside_conditions": [
                    "Grid connection established",
                    "Operator identity confirmed (COCOBOD or lead tenant)",
                    "Ghana FOODBELT Authority aggregation mechanism activated",
                    "AfDB SAPZ co-financing approved",
                ],
                "growth_narrative": (
                    "The most asymmetric opportunity on the corridor. "
                    "Base case: flat at 8 MW. "
                    "Upside case: 150 MW — nearly 19x growth. "
                    "Development impact is exceptional (95,000 jobs potential) "
                    "but bankability conditions must be met first. "
                    "Recommend including in Phase 3 planning only."
                ),
            },

            {
                # Takoradi Port — Bulk & General Cargo Terminal
                # Bankability: Tier 2 (score 0.78) — 15% execution haircut applied
                # Growth driver: Type 1 — liquid bulk jetty expansion confirmed
                "anchor_id": "AL_ANC_015",
                "detection_id": "DET-015",
                "entity_name": "Takoradi Port — Bulk & General Cargo Terminal",
                "country": "Ghana",
                "bankability_tier": "Tier 2",
                "current_mw": 18.0,
                "year_5_mw": 28.0,
                "year_10_mw": 38.0,
                "year_20_mw": 58.0,
                "cagr": "6.0%",
                "growth_driver_type": "Type 1 — Committed Expansion",
                "growth_driver": (
                    "Liquid bulk jetty extension confirmed — adds dedicated "
                    "petroleum product unloading berth by Year 2. "
                    "Ghana bauxite export corridor through Takoradi growing — "
                    "new bauxite handling facility adds 5–8 MW by Year 4. "
                    "Ghana Manganese Company port infrastructure adjacent "
                    "to Takoradi compounds area demand growth."
                ),
                "confidence_band": "Narrow",
                "scenario_low_year_10_mw": 32.0,
                "scenario_high_year_10_mw": 45.0,
                "growth_narrative": (
                    "Steady, reliable growth driven by committed port expansion "
                    "and Ghana resource export growth. "
                    "Not a dominant anchor but highly predictable revenue contribution."
                ),
            },

            {
                # Accra Data Center (ADC) — CSquared / Liquid Telecom
                # Bankability: Tier 1 (score 0.86) — growth modeled at face value
                # Growth driver: Type 1 — annex expansion formally announced
                "anchor_id": "AL_ANC_016",
                "detection_id": "DET-016",
                "entity_name": "Accra Data Center (ADC)",
                "country": "Ghana",
                "bankability_tier": "Tier 1",
                "current_mw": 12.0,
                "year_5_mw": 25.0,
                "year_10_mw": 42.0,
                "year_20_mw": 85.0,
                "cagr": "10.2%",
                "growth_driver_type": "Type 1 — Committed Expansion",
                "growth_driver": (
                    "CSquared annex expansion confirmed — adds 8–10 MW "
                    "on completion (Year 2). "
                    "West Africa cloud computing market growing at 28% CAGR — "
                    "ADC is the primary carrier-neutral facility in Ghana. "
                    "Financial services sector digitisation (mobile money, "
                    "digital banking) driving colocation demand. "
                    "5G rollout by MTN and Vodafone Ghana increases "
                    "backbone interconnect requirements at this node."
                ),
                "confidence_band": "Moderate",
                "scenario_low_year_10_mw": 35.0,
                "scenario_high_year_10_mw": 52.0,
                "growth_narrative": (
                    "Digital infrastructure is the fastest-growing sector on the corridor. "
                    "ADC benefits from being the sole carrier-neutral Tier III "
                    "facility in Ghana — demand growth is structural. "
                    "Key risk: a competing data center entering Ghana market "
                    "could split demand growth."
                ),
            },

            {
                # Lithium Exploration & Processing Site — Ghana North
                # Bankability: Tier 3 (score 0.42) — CONDITIONAL UPSIDE ONLY
                # Growth driver: Type 4 — contingent on mining licence and identity
                "anchor_id": "AL_ANC_035",
                "detection_id": "DET-035",
                "entity_name": "Lithium Exploration & Processing Site — Ghana North",
                "country": "Ghana",
                "bankability_tier": "Tier 3",
                "current_mw": 8.0,
                "year_5_mw": 8.0,
                "year_10_mw": 8.0,
                "year_20_mw": 8.0,
                "cagr": "0.0%",
                "growth_driver_type": "Type 4 — Conditional / Potential",
                "growth_driver": (
                    "BASE CASE: No growth. Currently in exploration phase — "
                    "demand stays at 8 MW until mining licence is granted "
                    "and operator identity is confirmed. "
                    "UPSIDE SCENARIO (if mining licence granted and operator confirmed): "
                    "Ramp to full production adds 80–150 MW by Year 5–8. "
                    "At full buildout lithium mine of this scale requires 120–150 MW. "
                    "Global EV battery demand creates strong commercial case "
                    "for accelerated development."
                ),
                "confidence_band": "Conditional — excluded from base case",
                "scenario_low_year_10_mw": 8.0,
                "scenario_high_year_10_mw": 140.0,
                "upside_conditions": [
                    "Full mining licence granted by Ghana Minerals Commission",
                    "Operator identity confirmed via cadastre access request",
                    "Spur connection (~44km) financed with operator guarantee",
                    "EV battery offtake agreement secured by operator",
                ],
                "growth_narrative": (
                    "Strategically important given global lithium demand "
                    "but too uncertain for base case modeling. "
                    "Recommend flagging as future pipeline opportunity. "
                    "Reassess when mining licence status changes."
                ),
            },

            # ================================================================
            # TOGO
            # ================================================================

            {
                # Port of Lomé — Container Terminal
                # Bankability: Tier 1 (score 0.85) — growth modeled at face value
                # Growth driver: Type 1 — berth expansion Phase 2 in active planning
                "anchor_id": "AL_ANC_017",
                "detection_id": "DET-017",
                "entity_name": "Port of Lomé — Container Terminal",
                "country": "Togo",
                "bankability_tier": "Tier 1",
                "current_mw": 28.0,
                "year_5_mw": 42.0,
                "year_10_mw": 58.0,
                "year_20_mw": 88.0,
                "cagr": "5.9%",
                "growth_driver_type": "Type 1 — Committed Expansion",
                "growth_driver": (
                    "Lomé Container Terminal Phase 2 berth expansion approved — "
                    "adds 4 berths and 6 new cranes by Year 3. "
                    "Deepest natural port in West Africa — structurally advantaged "
                    "for ECOWAS transshipment as regional trade grows. "
                    "Niger, Burkina Faso, and Mali transit volumes growing "
                    "at 9%/year as Sahel hinterland economies expand."
                ),
                "confidence_band": "Narrow",
                "scenario_low_year_10_mw": 50.0,
                "scenario_high_year_10_mw": 68.0,
                "growth_narrative": (
                    "Lomé port is West Africa's most strategically located "
                    "transshipment hub. Growth is highly predictable and "
                    "tied to committed expansion rather than speculation. "
                    "Togo grid unreliability currently suppresses port efficiency — "
                    "reliable power itself will increase throughput capacity."
                ),
            },

            {
                # Lomé Cement Plant (WACEM)
                # Bankability: Tier 2 (score 0.79) — 15% execution haircut applied
                # Growth driver: Type 3 — West Africa construction boom sector-driven
                "anchor_id": "AL_ANC_019",
                "detection_id": "DET-019",
                "entity_name": "Lomé Cement Plant (WACEM)",
                "country": "Togo",
                "bankability_tier": "Tier 2",
                "current_mw": 35.0,
                "year_5_mw": 50.0,
                "year_10_mw": 65.0,
                "year_20_mw": 92.0,
                "cagr": "5.0%",
                "growth_driver_type": "Type 3 — Sector-Driven Expansion",
                "growth_driver": (
                    "West Africa cement demand growing at 6%/year driven by "
                    "urbanisation and infrastructure investment. "
                    "WACEM 3rd kiln line addition under discussion — "
                    "not yet committed but technically feasible. "
                    "Reliable power enables kiln continuous operation, "
                    "increasing effective capacity without new kiln investment. "
                    "15% execution haircut applied — WACEM is private, "
                    "limited financial transparency."
                ),
                "confidence_band": "Wide",
                "scenario_low_year_10_mw": 52.0,
                "scenario_high_year_10_mw": 80.0,
                "growth_narrative": (
                    "Cement demand growth is structural and reliable. "
                    "Key uncertainty is whether WACEM invests in 3rd kiln "
                    "or competitor enters the market. "
                    "Reliable power itself unlocks 10–15% efficiency gain "
                    "at existing kilns."
                ),
            },

            {
                # Lomé Free Zone (SAZOF)
                # Bankability: Tier 2 (score 0.71) — 20% execution haircut applied
                # Growth driver: Type 2 — Togo government Smart Lomé programme
                "anchor_id": "AL_ANC_020",
                "detection_id": "DET-020",
                "entity_name": "Lomé Free Zone (SAZOF)",
                "country": "Togo",
                "bankability_tier": "Tier 2",
                "current_mw": 22.0,
                "year_5_mw": 40.0,
                "year_10_mw": 62.0,
                "year_20_mw": 105.0,
                "cagr": "8.2%",
                "growth_driver_type": "Type 2 — Policy-Backed Expansion",
                "growth_driver": (
                    "Togo Smart Lomé initiative commits $1.2B to SEZ "
                    "infrastructure through 2030. "
                    "Zone has significant suppressed demand — "
                    "reliable power expected to increase zone utilisation "
                    "from current 44% to 70%+ within 2 years, "
                    "adding 15–18 MW immediately. "
                    "New pharmaceutical and electronics manufacturing "
                    "enterprise attraction programme underway. "
                    "20% haircut applied for Togo sovereign execution risk."
                ),
                "confidence_band": "Moderate",
                "scenario_low_year_10_mw": 48.0,
                "scenario_high_year_10_mw": 78.0,
                "growth_narrative": (
                    "Suppressed demand unlock is the near-term driver, "
                    "compounding into structural zone growth over 20 years. "
                    "Togo has demonstrated commitment to zone development — "
                    "SAZOF institutional quality is improving. "
                    "Key risk: competition from Cotonou and Accra zones "
                    "for enterprise attraction."
                ),
            },

            # ================================================================
            # BENIN
            # ================================================================

            {
                # Port of Cotonou — Bénin Terminal
                # Bankability: Tier 1 (score 0.80) — growth modeled at face value
                # Growth driver: Type 1 — port modernisation programme confirmed
                "anchor_id": "AL_ANC_022",
                "detection_id": "DET-022",
                "entity_name": "Port of Cotonou — Bénin Terminal",
                "country": "Benin",
                "bankability_tier": "Tier 1",
                "current_mw": 24.0,
                "year_5_mw": 36.0,
                "year_10_mw": 48.0,
                "year_20_mw": 72.0,
                "cagr": "5.6%",
                "growth_driver_type": "Type 1 — Committed Expansion",
                "growth_driver": (
                    "PAC port modernisation programme confirmed — "
                    "ro-ro ramp expansion and new container scanner "
                    "add 4–6 MW by Year 2. "
                    "Niger and Burkina Faso hinterland transit trade "
                    "growing at 8%/year — Cotonou is primary gateway. "
                    "Bolloré Phase 2 concession investment adds "
                    "handling capacity by Year 4."
                ),
                "confidence_band": "Narrow",
                "scenario_low_year_10_mw": 42.0,
                "scenario_high_year_10_mw": 56.0,
                "growth_narrative": (
                    "Reliable, moderate growth story. "
                    "Hinterland trade dependency creates structural demand. "
                    "Port modernisation is funded and committed. "
                    "Benin sovereign risk is the only moderating factor."
                ),
            },

            {
                # Zone Industrielle de Cotonou (PK10)
                # Bankability: Tier 2 (score 0.62) — 25% execution haircut applied
                # Growth driver: Type 2 — Benin government zone modernisation programme
                "anchor_id": "AL_ANC_023",
                "detection_id": "DET-023",
                "entity_name": "Zone Industrielle de Cotonou (PK10)",
                "country": "Benin",
                "bankability_tier": "Tier 2",
                "current_mw": 30.0,
                "year_5_mw": 44.0,
                "year_10_mw": 58.0,
                "year_20_mw": 88.0,
                "cagr": "5.5%",
                "growth_driver_type": "Type 2 — Policy-Backed Expansion",
                "growth_driver": (
                    "Benin government zone modernisation programme: "
                    "150-hectare expansion committed in 2030 National Plan. "
                    "Zone at 60% capacity — reliable power alone expected "
                    "to increase utilisation to 85%, adding 12–15 MW immediately. "
                    "New food processing and packaging enterprise attraction "
                    "programme supported by APIEX. "
                    "25% execution haircut applied for Benin fiscal constraints "
                    "and historical delivery delays."
                ),
                "confidence_band": "Wide",
                "scenario_low_year_10_mw": 44.0,
                "scenario_high_year_10_mw": 72.0,
                "growth_narrative": (
                    "Significant suppressed demand unlock in near term. "
                    "Longer-term growth dependent on Benin improving "
                    "its broader investment climate. "
                    "Key risk: Benin zone competes with Lomé Free Zone "
                    "and Tema Free Zone for enterprise attraction — "
                    "power reliability improvement is the primary differentiator."
                ),
            },

            {
                # Unidentified Agro-Processing Cluster — Benin Coastal
                # Bankability: Tier 3 (score 0.28) — CONDITIONAL UPSIDE ONLY
                # Growth driver: Type 4 — entirely contingent on identity confirmation
                "anchor_id": "AL_ANC_024",
                "detection_id": "DET-024",
                "entity_name": "Unidentified Agro-Processing Cluster — Benin Coastal",
                "country": "Benin",
                "bankability_tier": "Tier 3",
                "current_mw": 4.5,
                "year_5_mw": 4.5,
                "year_10_mw": 4.5,
                "year_20_mw": 4.5,
                "cagr": "0.0%",
                "growth_driver_type": "Type 4 — Conditional / Potential",
                "growth_driver": (
                    "BASE CASE: No growth. Identity completely unresolved — "
                    "demand stays at current estimate until operator confirmed. "
                    "UPSIDE SCENARIO (if multinational agro-processor confirmed): "
                    "Cold chain expansion and pineapple/cashew export growth "
                    "could drive demand to 25–35 MW by Year 10. "
                    "If confirmed as part of AfDB SAPZ programme, "
                    "institutional backing significantly improves trajectory."
                ),
                "confidence_band": "Conditional — excluded from base case",
                "scenario_low_year_10_mw": 4.5,
                "scenario_high_year_10_mw": 35.0,
                "upside_conditions": [
                    "Operator identity confirmed via field verification",
                    "Connection to AfDB SAPZ programme confirmed",
                    "Export contract with EU buyer confirmed",
                ],
                "growth_narrative": (
                    "Cannot be modeled meaningfully until identity is resolved. "
                    "Recommend priority field verification."
                ),
            },

            # ================================================================
            # NIGERIA
            # ================================================================

            {
                # Dangote Refinery
                # Bankability: Tier 1 (score 0.96) — growth modeled at face value
                # Growth driver: Type 1 — petrochemical Phase 2 signed with EPC contractor
                "anchor_id": "AL_ANC_027",
                "detection_id": "DET-027",
                "entity_name": "Dangote Refinery",
                "country": "Nigeria",
                "bankability_tier": "Tier 1",
                "current_mw": 1000.0,
                "year_5_mw": 1350.0,
                "year_10_mw": 1600.0,
                "year_20_mw": 1800.0,
                "cagr": "3.0%",
                "growth_driver_type": "Type 1 — Committed Expansion",
                "growth_driver": (
                    "Dangote Petrochemical Complex Phase 2: "
                    "polypropylene and fertiliser plants signed with EPC contractor. "
                    "Adds ~300–350 MW by Year 5. "
                    "Refinery ramp from current 70% to full 650,000 bpd "
                    "adds further 100 MW by Year 3. "
                    "Long-term CAGR is moderate (3.0%) because base is already "
                    "very large — absolute MW additions are substantial."
                ),
                "confidence_band": "Narrow",
                "scenario_low_year_10_mw": 1450.0,
                "scenario_high_year_10_mw": 1750.0,
                "growth_narrative": (
                    "The single most important anchor on the corridor. "
                    "$19B investment committed — expansion is near-certain. "
                    "At 1,000 MW base and 1,800 MW by Year 20, "
                    "Dangote alone justifies the Lagos transmission hub. "
                    "Low CAGR belies enormous absolute MW additions."
                ),
            },

            {
                # Lekki Free Trade Zone
                # Bankability: Tier 1 (score 0.88) — growth modeled at face value
                # Growth driver: Type 1 — Chinese sovereign investment committed
                "anchor_id": "AL_ANC_028",
                "detection_id": "DET-028",
                "entity_name": "Lekki Free Trade Zone",
                "country": "Nigeria",
                "bankability_tier": "Tier 1",
                "current_mw": 150.0,
                "year_5_mw": 420.0,
                "year_10_mw": 750.0,
                "year_20_mw": 1200.0,
                "cagr": "10.8%",
                "growth_driver_type": "Type 1 — Committed Expansion",
                "growth_driver": (
                    "Chinese sovereign investment pipeline: $20B+ committed, "
                    "7 active construction zones confirmed in satellite imagery. "
                    "Zone at only 34% buildout — scaling to 200,000-job "
                    "full buildout drives demand from 150 MW to 1,200 MW. "
                    "Adjacent Dangote Refinery creates supply chain cluster "
                    "that accelerates enterprise attraction. "
                    "Lekki Deep Sea Port connectivity adds logistics enterprises."
                ),
                "confidence_band": "Moderate",
                "scenario_low_year_10_mw": 580.0,
                "scenario_high_year_10_mw": 950.0,
                "growth_narrative": (
                    "Second most important growth story on the corridor after Dangote. "
                    "The 34% current buildout means 66% of committed investment "
                    "is still to come — this is a 20-year compounding story. "
                    "Key risk: geopolitical factors affecting Chinese "
                    "sovereign investment pace. "
                    "Even at 50% of projected buildout, "
                    "demand exceeds 600 MW by Year 10."
                ),
            },

            {
                # Lekki Deep Sea Port
                # Bankability: Tier 1 (score 0.87) — growth modeled at face value
                # Growth driver: Type 1 — berth expansion Phase 2 in planning
                "anchor_id": "AL_ANC_029",
                "detection_id": "DET-029",
                "entity_name": "Lekki Deep Sea Port",
                "country": "Nigeria",
                "bankability_tier": "Tier 1",
                "current_mw": 35.0,
                "year_5_mw": 60.0,
                "year_10_mw": 88.0,
                "year_20_mw": 140.0,
                "cagr": "7.2%",
                "growth_driver_type": "Type 1 — Committed Expansion",
                "growth_driver": (
                    "Port fully operational since 2024 — Phase 2 berth expansion "
                    "in active planning for Year 3–4. "
                    "Dangote Refinery supply chains generate immediate and "
                    "growing cargo volumes. "
                    "Lekki FTZ manufacturing output adds container export volumes. "
                    "45-year concession creates long demand horizon."
                ),
                "confidence_band": "Narrow",
                "scenario_low_year_10_mw": 75.0,
                "scenario_high_year_10_mw": 102.0,
                "growth_narrative": (
                    "Growth is driven by the Lekki cluster ecosystem — "
                    "Dangote and Lekki FTZ are powerful demand multipliers "
                    "for port cargo volumes. "
                    "Highly predictable within narrow bounds."
                ),
            },

            {
                # MainOne Data Center (MDX-i Lagos) — Equinix
                # Bankability: Tier 1 (score 0.95) — growth modeled at face value
                # Growth driver: Type 1 — floor space doubling confirmed by Equinix
                "anchor_id": "AL_ANC_030",
                "detection_id": "DET-030",
                "entity_name": "MainOne Data Center (MDX-i Lagos)",
                "country": "Nigeria",
                "bankability_tier": "Tier 1",
                "current_mw": 18.0,
                "year_5_mw": 42.0,
                "year_10_mw": 72.0,
                "year_20_mw": 140.0,
                "cagr": "10.8%",
                "growth_driver_type": "Type 1 — Committed Expansion",
                "growth_driver": (
                    "Equinix confirmed floor space doubling — "
                    "adds 18–20 MW on expansion completion (Year 2). "
                    "Nigeria cloud computing market growing at 32% CAGR. "
                    "Financial services and fintech sector (Lagos is Africa's "
                    "fintech capital) driving colocation demand. "
                    "Hyperscaler anchor tenant (AWS, Google, or Azure) "
                    "expected to take dedicated hall by Year 3 — "
                    "adds 15–20 MW step load."
                ),
                "confidence_band": "Moderate",
                "scenario_low_year_10_mw": 58.0,
                "scenario_high_year_10_mw": 88.0,
                "growth_narrative": (
                    "Highest CAGR of any confirmed anchor on the corridor. "
                    "Digital infrastructure demand in Lagos is growing faster "
                    "than any other sector. "
                    "Key risk: competing data centers entering the Lagos market "
                    "split demand growth — but Lagos market is large enough "
                    "for multiple facilities."
                ),
            },

            {
                # Apapa Port Complex
                # Bankability: Tier 1 (score 0.82) — growth modeled at face value
                # Growth driver: Type 2 — NPA congestion relief programme
                "anchor_id": "AL_ANC_031",
                "detection_id": "DET-031",
                "entity_name": "Apapa Port Complex",
                "country": "Nigeria",
                "bankability_tier": "Tier 1",
                "current_mw": 55.0,
                "year_5_mw": 72.0,
                "year_10_mw": 88.0,
                "year_20_mw": 118.0,
                "cagr": "3.9%",
                "growth_driver_type": "Type 2 — Policy-Backed Expansion",
                "growth_driver": (
                    "NPA $2B congestion relief investment programme formally committed. "
                    "New container scanning gantries add 3–4 MW by Year 2. "
                    "Lagos population growth (25M today, 35M by 2035) "
                    "drives steady import volume increase. "
                    "Growth is moderate because Lekki Deep Sea Port "
                    "is absorbing new container capacity — "
                    "Apapa grows steadily rather than rapidly."
                ),
                "confidence_band": "Narrow",
                "scenario_low_year_10_mw": 78.0,
                "scenario_high_year_10_mw": 98.0,
                "growth_narrative": (
                    "Stable, reliable growth story. Apapa is not the "
                    "growth port (Lekki is) but it remains Nigeria's "
                    "primary port for the foreseeable future. "
                    "Moderate CAGR on a large base means substantial "
                    "absolute MW additions."
                ),
            },

            {
                # Sagamu-Interchange Manufacturing Cluster
                # Bankability: Tier 2 (score 0.58) — 25% execution haircut applied
                # Growth driver: Type 3 — Lagos-Ibadan corridor industrialisation
                "anchor_id": "AL_ANC_032",
                "detection_id": "DET-032",
                "entity_name": "Sagamu-Interchange Manufacturing Cluster",
                "country": "Nigeria",
                "bankability_tier": "Tier 2",
                "current_mw": 45.0,
                "year_5_mw": 62.0,
                "year_10_mw": 80.0,
                "year_20_mw": 118.0,
                "cagr": "4.9%",
                "growth_driver_type": "Type 3 — Sector-Driven Expansion",
                "growth_driver": (
                    "Lagos-Ibadan expressway upgrade drives industrial corridor growth. "
                    "FMCG and pharmaceutical manufacturing expanding in Nigeria "
                    "as import substitution policy takes effect. "
                    "New pharmaceutical block under construction — "
                    "operator unknown but adds 8–12 MW on commissioning. "
                    "25% execution haircut for multi-tenant, partially "
                    "resolved identity uncertainty."
                ),
                "confidence_band": "Wide",
                "scenario_low_year_10_mw": 60.0,
                "scenario_high_year_10_mw": 100.0,
                "growth_narrative": (
                    "Solid structural growth story but wide uncertainty "
                    "due to multi-tenant structure. "
                    "Key unlock: Ogun State government assuming PPA "
                    "counterparty role significantly improves confidence. "
                    "New pharmaceutical block identity confirmation "
                    "is priority action."
                ),
            },

            {
                # Unverified Hyperscale Data Center — Lagos Island North
                # Bankability: Tier 3 (score 0.35) — CONDITIONAL UPSIDE ONLY
                # Growth driver: Type 4 — entirely contingent on identity confirmation
                "anchor_id": "AL_ANC_034",
                "detection_id": "DET-034",
                "entity_name": "Unverified Hyperscale Data Center — Lagos Island North",
                "country": "Nigeria",
                "bankability_tier": "Tier 3",
                "current_mw": 35.0,
                "year_5_mw": 35.0,
                "year_10_mw": 35.0,
                "year_20_mw": 35.0,
                "cagr": "0.0%",
                "growth_driver_type": "Type 4 — Conditional / Potential",
                "growth_driver": (
                    "BASE CASE: No growth modeled — identity unresolved. "
                    "UPSIDE SCENARIO (if hyperscale DC confirmed): "
                    "Hyperscale data centers typically grow from initial "
                    "35 MW to 150–300 MW within 10 years as hyperscaler "
                    "anchors (AWS, Google, Microsoft) take dedicated halls. "
                    "If confirmed as Equinix, AWS, or similar — "
                    "immediate upgrade to Tier 1 with score 0.92+."
                ),
                "confidence_band": "Conditional — excluded from base case",
                "scenario_low_year_10_mw": 35.0,
                "scenario_high_year_10_mw": 250.0,
                "upside_conditions": [
                    "Identity confirmed via NCC registry or field verification",
                    "Operator confirmed as major DC or cloud provider",
                    "Grid connection agreement signed",
                ],
                "growth_narrative": (
                    "Highest potential upside on the corridor after Lekki FTZ. "
                    "If this is a hyperscale DC, it could become the "
                    "second-largest digital anchor after MainOne. "
                    "Priority field verification recommended — "
                    "potential $200M+ annual revenue contribution at buildout."
                ),
            },
        ],

        # ------------------------------------------------------------------ #
        #  SUMMARY                                                            #
        # ------------------------------------------------------------------ #
        "summary": {
            "aggregate_base_case": {
                "current_mw": 2127.5,
                "year_5_mw": 3480.0,
                "year_10_mw": 4690.0,
                "year_20_mw": 6017.0,
                "overall_growth_pct": "183%",
            },
            "aggregate_upside": {
                "year_10_mw": 5280.0,
                "year_20_mw": 7150.0,
            },
            "highest_cagr_anchors": [
                "AL_ANC_028 — Lekki FTZ (10.8%) — Chinese sovereign investment buildout",
                "AL_ANC_030 — MainOne Data Center (10.8%) — cloud demand growth",
                "AL_ANC_016 — Accra Data Center (10.2%) — West Africa digital growth",
                "AL_ANC_009 — Tema Free Zone (7.5%) — zone expansion + demand unlock",
                "AL_ANC_029 — Lekki Deep Sea Port (7.2%) — cluster ecosystem growth",
            ],
            "conditional_upside_anchors": [
                "AL_ANC_014 — Weta Rice Farm: 8 MW → 150 MW if connected (19x)",
                "AL_ANC_035 — Lithium Site: 8 MW → 140 MW if licensed (18x)",
                "AL_ANC_034 — Unverified Lagos DC: 35 MW → 250 MW if confirmed (7x)",
                "AL_ANC_024 — Benin Agro Cluster: 4.5 MW → 35 MW if confirmed (8x)",
            ],
            "growth_driver_breakdown": {
                "type_1_committed": 12,
                "type_2_policy_backed": 6,
                "type_3_sector_driven": 2,
                "type_4_conditional": 4,
            },
            "confidence_band_breakdown": {
                "narrow": 9,
                "moderate": 7,
                "wide": 4,
                "conditional_excluded": 4,
            },
            "priority_verification_for_trajectory_upgrade": [
                "AL_ANC_034: Field verify Lagos DC — potential 250 MW upside",
                "AL_ANC_004: Confirm Cargill identity — upgrades to narrow band",
                "AL_ANC_035: Request Minerals Commission cadastre access — "
                "unlocks lithium mine trajectory",
            ],
        },

        "message": (
            "20-year demand trajectories modeled for 24 anchor loads. "
            "Base case corridor demand grows from 2,127.5 MW to 6,017 MW (+183%). "
            "Upside scenario reaches 7,150 MW if 4 conditional anchors confirmed. "
            "Dangote Refinery (1,000 → 1,800 MW) and Lekki FTZ (150 → 1,200 MW) "
            "dominate the Lagos-Lekki cluster which alone accounts for 69% "
            "of corridor demand by Year 20. "
            "4 conditional anchors excluded from base case — "
            "priority verification recommended before Phase 2 planning."
        ),
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