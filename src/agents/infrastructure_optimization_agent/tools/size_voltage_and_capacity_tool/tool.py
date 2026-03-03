import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import CapacitySizingInput


@tool("size_voltage_and_capacity", description=TOOL_DESCRIPTION)
def size_voltage_and_capacity_tool(
    payload: CapacitySizingInput, runtime: ToolRuntime
) -> Command:
    """
    Determines optimal voltage class, conductor type, thermal capacity, and
    security standard for each transmission segment of the Abidjan-Lagos corridor.

    This is the first tool of the Infrastructure Optimization Agent. It takes
    the phased opportunity list from prioritize_opportunities and translates
    demand profiles into engineering specifications.

    Key engineering decisions per segment:

        Voltage class selection:
            33kV   — distribution-level spurs, <20 MW, <30km
            161kV  — medium-distance spurs, 20–150 MW, 30–120km
            225kV  — medium backbone, 150–400 MW, 100–250km (WAPP standard)
            330kV  — primary backbone, 400–1,500 MW, 200–600km (West Africa standard)
            400kV  — high-capacity backbone, >1,500 MW, 300–1,100km

        Security standard (N-x):
            N-0    — no redundancy; acceptable for Standard reliability class only
            N-1    — single contingency; loss of one circuit does not interrupt supply
                     mandatory for High reliability class anchors
            N-1-1  — enhanced contingency; mandatory for Critical reliability class
                     (underground mines, refineries, data centers, major ports)

        Conductor selection:
            ACSR    — Aluminium Conductor Steel Reinforced; standard overhead
            AAAC    — All Aluminium Alloy Conductor; coastal/high-humidity environments
            ACCC    — Aluminium Conductor Composite Core; high-temperature, sag-critical
            XLPE    — Cross-Linked Polyethylene; underground cable for urban / sensitive areas

        Surge Impedance Loading (SIL) is the natural power transfer capacity of a
        transmission line. Lines operating near SIL have minimum reactive power
        compensation requirements. SIL scales with voltage²:
            161kV → SIL ~75 MW
            225kV → SIL ~160 MW
            330kV → SIL ~340 MW
            400kV → SIL ~500 MW

    Inputs from upstream tools:
        prioritize_opportunities → phase, anchor cluster, current_mw, year_10_mw
        economic_gap_analysis    → segment distance, gap_type, severity
        route_optimization       → terrain profile, co-location %, highway overlap
        assess_bankability       → reliability_class per anchor (drives N-x standard)

    This tool does NOT return:
        - Tower placement coordinates   → plan_tower_placement
        - Substation layouts            → design_substations
        - Protection relay settings     → protection_relay_tool
        - Cost estimates                → capex_estimation_tool
    """

    response = {
        "corridor_id": "AL_CORRIDOR_POC_001",
        "corridor_length_km": 1080.0,
        "total_segments": 12,
        "sizing_philosophy": (
            "Each segment is sized to carry Year 10 peak demand with 20% headroom "
            "for growth to Year 20, while meeting the N-x security standard required "
            "by the highest reliability class anchor served by that segment. "
            "Voltage class is selected to minimize total lifetime cost (CAPEX + losses) "
            "over the 40-year asset life. Where segments serve Critical-class anchors, "
            "N-1-1 double-circuit configuration is mandatory regardless of cost premium."
        ),

        # ================================================================
        # BACKBONE SEGMENTS — Primary transmission spine
        # ================================================================
        "backbone_segments": [

            {
                # --------------------------------------------------------
                # SEGMENT 1: Abidjan Hub → Takoradi Hub
                # The longest single segment — the missing coastal link (GAP_001)
                # Serves: Abidjan cluster (AL_ANC_003, AL_ANC_005)
                #         Takoradi cluster (AL_ANC_015)
                # --------------------------------------------------------
                "segment_id": "SEG_BB_001",
                "gap_id": "GAP_001",
                "phase": "Phase 1",
                "name": "Abidjan Hub — Takoradi Hub (Coastal Backbone)",
                "from_node": "Vridi 225kV Substation, Abidjan, Côte d'Ivoire",
                "to_node": "Aboadze 330kV Substation, Takoradi, Ghana",
                "route_length_km": 382.0,
                "highway_co_location_pct": 55.0,
                "countries_traversed": ["Côte d'Ivoire", "Ghana"],

                "demand_profile": {
                    "current_mw": 105.0,
                    "year_5_mw": 170.0,
                    "year_10_mw": 230.0,
                    "year_20_mw": 320.0,
                    "sizing_target_mw": 276.0,   # Year 10 + 20% headroom
                },

                "voltage_selection": {
                    "recommended_voltage_kv": 330,
                    "alternatives_considered": [
                        {
                            "voltage_kv": 225,
                            "rejected_reason": (
                                "Insufficient for Year 10 demand — 225kV max thermal "
                                "capacity ~400 MW single circuit, but N-1 requirement "
                                "means effective capacity only ~200 MW. "
                                "Inadequate for Year 10 + headroom target of 276 MW "
                                "without double-circuit which costs nearly as much as 330kV."
                            ),
                        },
                        {
                            "voltage_kv": 400,
                            "rejected_reason": (
                                "Economically excessive for this segment demand level. "
                                "400kV SIL is ~500 MW — over-designed for 276 MW target. "
                                "Upgrade path from 330kV to 400kV feasible in Year 15+ "
                                "if Abidjan–Takoradi coastal demand exceeds 800 MW."
                            ),
                        },
                    ],
                    "voltage_selection_rationale": (
                        "330kV is the correct voltage for a 382km segment carrying "
                        "105–320 MW over 20 years. SIL at 330kV is ~340 MW — "
                        "the line operates near SIL which minimises reactive power "
                        "compensation. WAPP 330kV standard is established in Ghana "
                        "and Côte d'Ivoire — compatible with both countries' grids. "
                        "Line losses at 330kV over 382km: ~2.8% at full load. "
                        "At 225kV same distance losses would be ~7.1% — "
                        "the additional 4.3% loss represents ~$4.5M/year wasted revenue."
                    ),
                },

                "security_standard": {
                    "required_standard": "N-1",
                    "configuration": "Single-circuit with switching stations at 120km intervals",
                    "rationale": (
                        "Highest reliability class on this segment is High (Takoradi Port, "
                        "Abidjan Port). N-1 is sufficient — loss of the line triggers "
                        "graceful load shedding with switching to alternative supply paths. "
                        "N-1-1 not required as no Critical-class anchors are exclusively "
                        "served by this segment (Abidjan anchors have alternative supply)."
                    ),
                },

                "conductor_specification": {
                    "type": "AAAC — All Aluminium Alloy Conductor",
                    "size": "AAAC 560mm²",
                    "bundle": "Twin-bundle (2 × AAAC 560mm²)",
                    "thermal_rating_mw": 520.0,
                    "surge_impedance_loading_mw": 340.0,
                    "rationale": (
                        "AAAC selected over standard ACSR for coastal environment — "
                        "salt spray and high humidity along the Gulf of Guinea coastline "
                        "causes accelerated steel core corrosion in ACSR over 40-year life. "
                        "AAAC all-aluminium construction eliminates galvanic corrosion risk. "
                        "Twin-bundle provides 520 MW thermal rating — "
                        "sufficient for Year 20 demand of 320 MW with 63% headroom. "
                        "Twin-bundle also reduces radio interference and audible noise "
                        "near coastal settlements."
                    ),
                },

                "reactive_power_compensation": {
                    "required": True,
                    "type": "Fixed shunt reactors + SVCs",
                    "location": "Abidjan end, mid-point (Takoradi–Accra junction), Takoradi end",
                    "rationale": (
                        "382km at 330kV generates significant charging current (~120 MVAr). "
                        "Shunt reactors at each end absorb charging current during light load. "
                        "SVCs (Static VAr Compensators) provide dynamic voltage support "
                        "at midpoint switching station."
                    ),
                },

                "special_considerations": [
                    "Border crossing: Côte d'Ivoire / Ghana at Elubo — "
                    "joint ministerial approval required from both energy ministries",
                    "Environmental: Ankasa Resource Reserve (Ghana) requires 8km deviation — "
                    "underground XLPE cable section for 12km to avoid reserve buffer zone",
                    "Coastal erosion risk at 3 locations near Half Assini — "
                    "tower foundations require pile-driven design to 12m depth",
                ],
            },

            {
                # --------------------------------------------------------
                # SEGMENT 2: Takoradi Hub → Tema/Accra Hub
                # Existing WAPP 161kV line upgrade — connects to Ghana backbone
                # Serves: Tema cluster (AL_ANC_007, AL_ANC_008, AL_ANC_009, AL_ANC_016)
                # --------------------------------------------------------
                "segment_id": "SEG_BB_002",
                "gap_id": "GAP_006",
                "phase": "Phase 1",
                "name": "Takoradi Hub — Tema/Accra Hub (Ghana Backbone Upgrade)",
                "from_node": "Aboadze 330kV Substation, Takoradi",
                "to_node": "Tema Industrial 330kV Substation, Greater Accra",
                "route_length_km": 235.0,
                "highway_co_location_pct": 68.0,
                "countries_traversed": ["Ghana"],

                "demand_profile": {
                    "current_mw": 200.0,    # Tema cluster + Takoradi port
                    "year_5_mw": 320.0,
                    "year_10_mw": 420.0,
                    "year_20_mw": 580.0,
                    "sizing_target_mw": 504.0,   # Year 10 + 20% headroom
                },

                "voltage_selection": {
                    "recommended_voltage_kv": 330,
                    "alternatives_considered": [
                        {
                            "voltage_kv": 161,
                            "rejected_reason": (
                                "Existing 161kV line is at capacity — upgrade to "
                                "330kV required. At 161kV, 504 MW target would "
                                "require 4-circuit construction, more expensive "
                                "than single 330kV double-circuit."
                            ),
                        },
                    ],
                    "voltage_selection_rationale": (
                        "330kV upgrade of existing Takoradi–Tema 161kV corridor. "
                        "GRIDCo Ghana national plan already specifies this upgrade — "
                        "corridor project accelerates and co-funds an already-planned "
                        "national infrastructure investment. "
                        "Existing tower footings at 70% of locations can be reused "
                        "with head-frame replacement — reduces civil CAPEX by ~35%. "
                        "Line losses at 330kV over 235km: ~1.8% vs 4.6% at 161kV."
                    ),
                },

                "security_standard": {
                    "required_standard": "N-1-1",
                    "configuration": "Double-circuit on common towers",
                    "rationale": (
                        "Tema cluster includes Critical-class anchors: "
                        "Tema Port MPS (AL_ANC_008) and Tema Free Zone (AL_ANC_009). "
                        "N-1-1 mandatory — loss of one circuit must not interrupt "
                        "port operations. Double-circuit on common towers is the "
                        "standard solution; surviving circuit carries full load "
                        "under N-1 contingency."
                    ),
                },

                "conductor_specification": {
                    "type": "AAAC — All Aluminium Alloy Conductor",
                    "size": "AAAC 560mm²",
                    "bundle": "Twin-bundle per circuit (2 circuits = 4 sub-conductors total)",
                    "thermal_rating_mw": 520.0,
                    "surge_impedance_loading_mw": 340.0,
                    "rationale": (
                        "Double-circuit twin-bundle configuration. "
                        "Each circuit rated 520 MW — N-1 contingency leaves full "
                        "504 MW available on surviving circuit. "
                        "AAAC for coastal Ghana humidity. "
                        "Common tower double-circuit reduces land use and visual impact "
                        "compared to two separate single-circuit routes."
                    ),
                },

                "reactive_power_compensation": {
                    "required": True,
                    "type": "Shunt reactors at both ends",
                    "location": "Takoradi end and Tema Industrial substation",
                    "rationale": (
                        "235km charging current requires compensation at both ends. "
                        "Existing Aboadze shunt reactors may be reusable — "
                        "field assessment required."
                    ),
                },

                "special_considerations": [
                    "GRIDCo coordination required — this segment is on GRIDCo's "
                    "national transmission masterplan; joint development agreement needed",
                    "Existing tower reuse assessment: 70% reusable saves ~$45M CAPEX",
                    "Tema Industrial substation: new 330/161kV transformer bays required "
                    "to interface with existing 161kV Tema distribution network",
                ],
            },

            {
                # --------------------------------------------------------
                # SEGMENT 3: Tema Hub → Lomé Hub
                # Crosses Ghana/Togo border — new construction
                # Serves: Lomé cluster (AL_ANC_017, AL_ANC_019, AL_ANC_020)
                # --------------------------------------------------------
                "segment_id": "SEG_BB_003",
                "gap_id": "GAP_002",
                "phase": "Phase 1",
                "name": "Tema Hub — Lomé Hub (Ghana–Togo Coastal Backbone)",
                "from_node": "Tema Industrial 330kV Substation, Ghana",
                "to_node": "Tokoin 330kV Substation, Lomé, Togo",
                "route_length_km": 178.0,
                "highway_co_location_pct": 72.0,
                "countries_traversed": ["Ghana", "Togo"],

                "demand_profile": {
                    "current_mw": 85.0,
                    "year_5_mw": 138.0,
                    "year_10_mw": 185.0,
                    "year_20_mw": 265.0,
                    "sizing_target_mw": 222.0,
                },

                "voltage_selection": {
                    "recommended_voltage_kv": 330,
                    "voltage_selection_rationale": (
                        "330kV provides adequate capacity for this segment "
                        "while maintaining compatibility with both Ghana's GRIDCo "
                        "330kV network and the planned Togo 330kV backbone. "
                        "178km at 330kV: losses ~1.4% at full load. "
                        "Single circuit with N-1 switching — Lomé port can be "
                        "temporarily supplied from alternative paths during maintenance."
                    ),
                },

                "security_standard": {
                    "required_standard": "N-1",
                    "configuration": "Single-circuit with automatic reclosing",
                    "rationale": (
                        "Lomé port (AL_ANC_017) is Critical class but has "
                        "alternative supply paths from Togo national grid during "
                        "short outages. Single circuit with fast automatic reclosing "
                        "(< 1 second for transient faults) meets the reliability "
                        "requirement cost-effectively for this distance."
                    ),
                },

                "conductor_specification": {
                    "type": "AAAC — All Aluminium Alloy Conductor",
                    "size": "AAAC 560mm²",
                    "bundle": "Twin-bundle",
                    "thermal_rating_mw": 520.0,
                    "surge_impedance_loading_mw": 340.0,
                    "rationale": (
                        "AAAC coastal specification. "
                        "Twin-bundle provides headroom well beyond Year 20 demand."
                    ),
                },

                "reactive_power_compensation": {
                    "required": True,
                    "type": "Shunt reactors at both ends",
                    "location": "Tema end and Tokoin Lomé substation",
                },

                "special_considerations": [
                    "Border crossing: Ghana / Togo at Aflao/Lomé — "
                    "requires WAPP cross-border interconnection agreement",
                    "Aflao urban area: 14km underground XLPE section through "
                    "Aflao/Lomé border town — overhead construction not feasible",
                    "Togo ARSE regulatory approval required for new transmission asset",
                ],
            },

            {
                # --------------------------------------------------------
                # SEGMENT 4: Lomé Hub → Cotonou Hub
                # Closes the Lomé–Cotonou gap (GAP_002 eastern half)
                # Serves: Cotonou cluster (AL_ANC_022, AL_ANC_023)
                # --------------------------------------------------------
                "segment_id": "SEG_BB_004",
                "gap_id": "GAP_002",
                "phase": "Phase 2",
                "name": "Lomé Hub — Cotonou Hub (Togo–Benin Coastal Backbone)",
                "from_node": "Tokoin 330kV Substation, Lomé, Togo",
                "to_node": "Maria Gleta 330kV Substation, Cotonou, Benin",
                "route_length_km": 142.0,
                "highway_co_location_pct": 78.0,
                "countries_traversed": ["Togo", "Benin"],

                "demand_profile": {
                    "current_mw": 54.0,
                    "year_5_mw": 80.0,
                    "year_10_mw": 106.0,
                    "year_20_mw": 162.0,
                    "sizing_target_mw": 127.0,
                },

                "voltage_selection": {
                    "recommended_voltage_kv": 330,
                    "voltage_selection_rationale": (
                        "Although 127 MW target could technically be served by 225kV, "
                        "330kV is selected for three reasons: "
                        "(1) Continuity with Lomé Hub voltage — no transformation needed. "
                        "(2) Provides capacity for Benin import replacement — "
                        "Benin currently imports 85% of electricity; backbone enables "
                        "future import reduction as regional generation grows. "
                        "(3) WAPP 330kV standard — future interconnection to Nigeria "
                        "via 330kV requires this voltage at the Cotonou endpoint."
                    ),
                },

                "security_standard": {
                    "required_standard": "N-1",
                    "configuration": "Single-circuit with switching station at midpoint (Porto-Novo)",
                    "rationale": (
                        "Cotonou port (AL_ANC_022) is Critical class but alternative "
                        "supply from Maria Gleta plant provides backup during short outages. "
                        "Midpoint switching station at Porto-Novo (~70km) allows "
                        "sectionalising faults and restoring supply to either end "
                        "within 15 minutes."
                    ),
                },

                "conductor_specification": {
                    "type": "AAAC — All Aluminium Alloy Conductor",
                    "size": "AAAC 400mm²",
                    "bundle": "Single conductor",
                    "thermal_rating_mw": 280.0,
                    "surge_impedance_loading_mw": 310.0,
                    "rationale": (
                        "Single conductor 400mm² adequate for 127 MW target with "
                        "120% headroom to Year 20. "
                        "Smaller than other backbone segments reflecting lower "
                        "demand on this segment vs Lagos and Ghana. "
                        "Upgrade to twin-bundle feasible in Year 15 by adding "
                        "second sub-conductor to existing towers."
                    ),
                },

                "reactive_power_compensation": {
                    "required": True,
                    "type": "Shunt reactors at both ends",
                    "location": "Tokoin and Maria Gleta substations",
                },

                "special_considerations": [
                    "Border crossing: Togo / Benin — WAPP interconnection agreement required",
                    "Porto-Novo urban area: 6km underground section",
                    "Benin ABERME approval required for transmission asset",
                ],
            },

            {
                # --------------------------------------------------------
                # SEGMENT 5: Cotonou Hub → Lagos/Lekki Hub
                # Longest Nigerian segment — crosses Benin/Nigeria border
                # Serves: Lekki cluster (AL_ANC_027, AL_ANC_028, AL_ANC_029)
                #         Apapa (AL_ANC_031)
                # --------------------------------------------------------
                "segment_id": "SEG_BB_005",
                "gap_id": "GAP_003",
                "phase": "Phase 1",
                "name": "Cotonou Hub — Lagos/Lekki Hub (Benin–Nigeria Backbone)",
                "from_node": "Maria Gleta 330kV Substation, Cotonou, Benin",
                "to_node": "Lekki 400kV Hub, Lagos State, Nigeria",
                "route_length_km": 152.0,
                "highway_co_location_pct": 62.0,
                "countries_traversed": ["Benin", "Nigeria"],

                "demand_profile": {
                    "current_mw": 1293.0,   # Lekki cluster + Apapa
                    "year_5_mw": 1504.0,
                    "year_10_mw": 2448.0,
                    "year_20_mw": 4160.0,
                    "sizing_target_mw": 2938.0,   # Year 10 + 20% headroom
                },

                "voltage_selection": {
                    "recommended_voltage_kv": 400,
                    "alternatives_considered": [
                        {
                            "voltage_kv": 330,
                            "rejected_reason": (
                                "330kV max thermal capacity per double-circuit ~1,040 MW. "
                                "Year 10 target of 2,938 MW requires three 330kV circuits — "
                                "more expensive and complex than single 400kV double-circuit. "
                                "400kV double-circuit delivers 2,400 MW thermal capacity "
                                "with upgrade path to 3,600 MW via conductor replacement alone."
                            ),
                        },
                    ],
                    "voltage_selection_rationale": (
                        "400kV is the only technically and economically justified voltage "
                        "for this segment given the Lekki cluster demand profile. "
                        "Dangote Refinery alone is 1,000 MW — the segment must handle "
                        "this load plus Lekki FTZ growth to 1,200 MW. "
                        "400kV SIL is ~500 MW; double-circuit achieves 1,000 MW SIL — "
                        "the line operates efficiently near its natural loading point. "
                        "This is the only 400kV segment on the corridor — "
                        "all other segments are 330kV, minimising transformation losses. "
                        "400/330kV interface transformers at Lekki hub and Cotonou end. "
                        "Line losses at 400kV over 152km: ~0.9% — "
                        "significantly better than 330kV (~1.5%) at this demand level."
                    ),
                },

                "security_standard": {
                    "required_standard": "N-1-1",
                    "configuration": "Double-circuit on separate tower lines (not common towers)",
                    "rationale": (
                        "Dangote Refinery (AL_ANC_027) is Critical class — "
                        "1,000 MW refinery shutdown costs $24M/day. "
                        "N-1-1 on separate tower routes means even complete loss "
                        "of one tower line (storm, sabotage, etc.) leaves the "
                        "second route fully intact. "
                        "Common tower double-circuit rejected — single tower failure "
                        "or right-of-way incident would interrupt both circuits simultaneously. "
                        "Separate routing adds ~15% CAPEX but is non-negotiable "
                        "for a 1,000 MW Critical-class anchor."
                    ),
                },

                "conductor_specification": {
                    "type": "ACCC — Aluminium Conductor Composite Core",
                    "size": "ACCC 750mm²",
                    "bundle": "Quad-bundle per circuit (4 × ACCC 750mm²)",
                    "thermal_rating_mw": 2400.0,
                    "surge_impedance_loading_mw": 1000.0,
                    "rationale": (
                        "ACCC selected for this highest-demand segment: "
                        "composite core is lighter than steel, allowing longer span lengths "
                        "(fewer towers) and higher operating temperatures (more capacity). "
                        "Quad-bundle provides 2,400 MW thermal rating per circuit — "
                        "sufficient for full Lekki buildout demand of 4,160 MW by Year 20 "
                        "across two circuits (2 × 2,400 MW = 4,800 MW total). "
                        "ACCC reduces sag by 40% vs ACSR at same temperature — "
                        "critical for Lagos coastal zone where tower heights are constrained "
                        "by aviation regulations near Murtala Muhammed Airport approach paths."
                    ),
                },

                "reactive_power_compensation": {
                    "required": True,
                    "type": "SVCs at both ends + midpoint STATCOM",
                    "location": "Maria Gleta 400kV end, Lekki hub, midpoint at Badagry",
                    "rationale": (
                        "At 400kV and 2,400 MW load, dynamic reactive power management "
                        "is critical. SVCs provide fast voltage support during load changes. "
                        "Midpoint STATCOM at Badagry (76km from each end) maintains "
                        "voltage profile along segment during partial loading."
                    ),
                },

                "special_considerations": [
                    "Border crossing: Benin / Nigeria at Seme/Badagry — "
                    "ECOWAS energy protocol + bilateral Nigeria-Benin agreement required",
                    "Lagos aviation zone: tower height restricted to 60m within "
                    "15km of Murtala Muhammed Airport — longer spans required, "
                    "ACCC composite core enables this without additional towers",
                    "Lagos Island urban section: 22km underground XLPE 400kV cable "
                    "from Badagry to Lekki hub — most expensive single component "
                    "at ~$85M for 22km",
                    "NERC Nigeria approval required for cross-border interconnection",
                    "TCN coordination: Lekki hub must interface with TCN 330kV ring",
                ],
            },
        ],

        # ================================================================
        # SPUR SEGMENTS — Dedicated connections to specific anchor loads
        # ================================================================
        "spur_segments": [

            {
                # --------------------------------------------------------
                # SPUR 1: Obuasi Gold Mine Dedicated Spur
                # AngloGold Ashanti corporate guarantee anchors financing
                # --------------------------------------------------------
                "segment_id": "SEG_SP_001",
                "gap_id": "GAP_004",
                "phase": "Phase 1",
                "name": "Kumasi Hub — Obuasi Gold Mine Dedicated Spur",
                "anchor_served": "AL_ANC_012",
                "from_node": "Kumasi 330kV Substation, Ashanti Region, Ghana",
                "to_node": "Obuasi Mine 330/11kV Substation",
                "route_length_km": 98.0,
                "highway_co_location_pct": 38.0,

                "demand_profile": {
                    "current_mw": 68.0,
                    "year_5_mw": 88.0,
                    "year_10_mw": 108.0,
                    "year_20_mw": 140.0,
                    "sizing_target_mw": 130.0,
                },

                "voltage_selection": {
                    "recommended_voltage_kv": 161,
                    "voltage_selection_rationale": (
                        "161kV is the correct voltage for a 98km spur serving "
                        "68–140 MW over 20 years. "
                        "330kV would be over-engineered — SIL of 340 MW far exceeds "
                        "130 MW target, resulting in excessive reactive power generation "
                        "at light load requiring permanent reactor compensation. "
                        "161kV SIL ~75 MW; twin-bundle 161kV reaches 150 MW — "
                        "adequate with natural loading near SIL. "
                        "Line losses at 161kV over 98km: ~2.1% vs ~0.9% at 330kV — "
                        "acceptable given shorter spur length."
                    ),
                },

                "security_standard": {
                    "required_standard": "N-1-1",
                    "configuration": "Double-circuit 161kV on common towers",
                    "rationale": (
                        "Obuasi underground mine (AL_ANC_012) is Critical class — "
                        "power outage during underground operations is a safety emergency. "
                        "N-1-1 mandatory regardless of cost premium. "
                        "Double-circuit on common towers is acceptable here "
                        "(unlike SEG_BB_005) because mine has on-site diesel emergency backup "
                        "that covers the short window between tower failure and repair. "
                        "Mine also has step-down to 11kV on-site with automatic changeover."
                    ),
                },

                "conductor_specification": {
                    "type": "ACSR — Aluminium Conductor Steel Reinforced",
                    "size": "ACSR 400mm² (Zebra)",
                    "bundle": "Twin-bundle per circuit",
                    "thermal_rating_mw": 160.0,
                    "surge_impedance_loading_mw": 82.0,
                    "rationale": (
                        "ACSR acceptable for inland Ashanti Region — "
                        "no coastal corrosion risk, ACSR cost advantage justifiable. "
                        "Zebra 400mm² twin-bundle: 160 MW thermal rating per circuit — "
                        "both circuits available in normal operation (N-0 = 320 MW), "
                        "N-1 contingency leaves 160 MW on surviving circuit — "
                        "adequate for 130 MW target under contingency."
                    ),
                },

                "reactive_power_compensation": {
                    "required": False,
                    "rationale": (
                        "98km at 161kV generates ~22 MVAr charging current — "
                        "absorbed by mine's on-site reactive power compensation "
                        "equipment. No additional line compensation required."
                    ),
                },

                "special_considerations": [
                    "AngloGold Ashanti owns land along 34km of the spur route — "
                    "right-of-way cost significantly reduced",
                    "Obuasi Forest Reserve: 12km section requires offset routing "
                    "and ESIA Category B assessment",
                    "Mine 11kV distribution upgrade required to interface with "
                    "new 161kV substation — AngloGold Ashanti scope",
                ],
            },

            {
                # --------------------------------------------------------
                # SPUR 2: Volta Agricultural Belt Grid Connection
                # Catalytic spur — unlocks 100,000 ha irrigation potential
                # --------------------------------------------------------
                "segment_id": "SEG_SP_002",
                "gap_id": "GAP_011",
                "phase": "Phase 2",
                "name": "Akuse Hub — Volta Agricultural Belt Spur",
                "anchor_served": "AL_ANC_014",
                "from_node": "Akuse 161kV Substation, Volta Region, Ghana",
                "to_node": "Weta Zone 161/33kV Substation",
                "route_length_km": 35.0,
                "highway_co_location_pct": 22.0,

                "demand_profile": {
                    "current_mw": 8.0,
                    "year_5_mw": 8.0,
                    "year_10_mw": 8.0,         # Base case flat until conditions met
                    "year_20_mw": 150.0,        # Upside if irrigation expansion confirmed
                    "sizing_target_mw": 180.0,  # Sized for upside — cheap to build big here
                },

                "voltage_selection": {
                    "recommended_voltage_kv": 161,
                    "voltage_selection_rationale": (
                        "161kV selected despite current 8 MW demand because "
                        "the spur is sized for the 150 MW upside scenario. "
                        "At 35km, building 161kV vs 33kV costs only $4M more — "
                        "a trivial premium to avoid rebuilding at higher voltage "
                        "when irrigation demand materialises. "
                        "Build once, sized for buildout — standard practice for "
                        "agricultural electrification spurs with confirmed upside potential."
                    ),
                },

                "security_standard": {
                    "required_standard": "N-0",
                    "configuration": "Single-circuit with manual switching",
                    "rationale": (
                        "Weta Rice Farm (AL_ANC_014) is Standard reliability class — "
                        "seasonal agricultural operations can tolerate planned outages. "
                        "N-0 single circuit acceptable. "
                        "Upgrade to N-1 double-circuit when demand exceeds 50 MW "
                        "and reliability class is upgraded."
                    ),
                },

                "conductor_specification": {
                    "type": "ACSR — Aluminium Conductor Steel Reinforced",
                    "size": "ACSR 300mm² (Panther)",
                    "bundle": "Single conductor",
                    "thermal_rating_mw": 100.0,
                    "surge_impedance_loading_mw": 68.0,
                    "rationale": (
                        "Single Panther ACSR for current 8 MW demand with upgrade path. "
                        "100 MW thermal rating provides headroom for early irrigation expansion. "
                        "Second conductor can be strung on existing towers when "
                        "demand exceeds 80 MW — incremental CAPEX only."
                    ),
                },

                "reactive_power_compensation": {
                    "required": False,
                    "rationale": "35km at 161kV — charging current absorbed by substation equipment.",
                },

                "special_considerations": [
                    "CONDITIONAL — do not begin construction until: "
                    "(1) Weta operator identity confirmed, "
                    "(2) AfDB SAPZ co-financing approved, "
                    "(3) COCOBOD aggregation PPA signed",
                    "Route crosses Volta River floodplain — 8km section requires "
                    "elevated tower design (18m minimum height) for flood clearance",
                ],
            },

            {
                # --------------------------------------------------------
                # SPUR 3: Lithium Site Dedicated Spur
                # Conditional — operator and licence required
                # --------------------------------------------------------
                "segment_id": "SEG_SP_003",
                "gap_id": "GAP_005",
                "phase": "Phase 3",
                "name": "Mampong Hub — Lithium Site Dedicated Spur",
                "anchor_served": "AL_ANC_035",
                "from_node": "Mampong 161kV Substation, Ashanti/Brong-Ahafo, Ghana",
                "to_node": "Lithium Site 161/33kV Substation (planned)",
                "route_length_km": 44.0,
                "highway_co_location_pct": 18.0,

                "demand_profile": {
                    "current_mw": 8.0,
                    "year_5_mw": 8.0,
                    "year_10_mw": 8.0,
                    "year_20_mw": 140.0,
                    "sizing_target_mw": 168.0,
                },

                "voltage_selection": {
                    "recommended_voltage_kv": 161,
                    "voltage_selection_rationale": (
                        "161kV sized for full mining production scenario (140 MW). "
                        "CONDITIONAL — do not commit to construction until "
                        "mining licence granted and operator confirmed."
                    ),
                },

                "security_standard": {
                    "required_standard": "N-1",
                    "configuration": "Double-circuit 161kV",
                    "rationale": (
                        "Underground lithium mine at full production will require "
                        "High or Critical reliability — N-1 pre-specified. "
                        "Exact standard confirmed when operator and mine design finalised."
                    ),
                },

                "conductor_specification": {
                    "type": "ACSR — Aluminium Conductor Steel Reinforced",
                    "size": "ACSR 400mm² (Zebra)",
                    "bundle": "Single conductor initially, twin-bundle at full production",
                    "thermal_rating_mw": 160.0,
                    "surge_impedance_loading_mw": 82.0,
                    "rationale": (
                        "Single Zebra initially for exploration phase (8 MW). "
                        "Tower design allows twin-bundle addition without reconstruction."
                    ),
                },

                "reactive_power_compensation": {
                    "required": False,
                    "rationale": "44km at 161kV manageable without additional compensation.",
                },

                "special_considerations": [
                    "CONDITIONAL — do not proceed until: "
                    "(1) Mining licence granted by Ghana Minerals Commission, "
                    "(2) Operator identity confirmed, "
                    "(3) Operator corporate guarantee secured for spur financing",
                    "No highway co-location available — greenfield route through "
                    "agricultural land requires full ESIA Category B assessment",
                ],
            },
        ],

        # ================================================================
        # DISTRIBUTION REINFORCEMENTS — Industrial zone feeders
        # ================================================================
        "distribution_reinforcements": [

            {
                "segment_id": "SEG_DR_001",
                "gap_id": "GAP_007",
                "phase": "Phase 1",
                "name": "Lomé Industrial Dedicated 161kV Feeder",
                "anchors_served": ["AL_ANC_017", "AL_ANC_019", "AL_ANC_020"],
                "voltage_kv": 161,
                "configuration": "Ring main — port, cement plant, free zone",
                "length_km": 18.0,
                "capacity_mw": 200.0,
                "security_standard": "N-1",
                "conductor_type": "XLPE 400mm² underground (port area) + ACSR overhead",
                "rationale": (
                    "Dedicated 161kV industrial feeder ring-fenced from residential Togo grid. "
                    "Port, cement plant, and free zone on same ring — any section fault "
                    "is isolated while rest of ring continues to supply. "
                    "Underground XLPE in port and free zone areas, "
                    "overhead ACSR between zones."
                ),
            },

            {
                "segment_id": "SEG_DR_002",
                "gap_id": "GAP_008",
                "phase": "Phase 2",
                "name": "Zone Industrielle Cotonou Dedicated 33kV Feeder",
                "anchors_served": ["AL_ANC_023"],
                "voltage_kv": 33,
                "configuration": "Dedicated feeder from Maria Gleta 330kV substation",
                "length_km": 8.0,
                "capacity_mw": 65.0,
                "security_standard": "N-1",
                "conductor_type": "XLPE 300mm² underground",
                "power_quality_equipment": "STATCOM 50 MVAr for voltage stabilisation",
                "rationale": (
                    "Separates industrial zone from chronic Benin residential grid instability. "
                    "Dedicated feeder + STATCOM delivers ±1.5% voltage regulation — "
                    "within industrial equipment tolerance. "
                    "Underground XLPE through urban Cotonou."
                ),
            },

            {
                "segment_id": "SEG_DR_003",
                "gap_id": "GAP_009",
                "phase": "Phase 2",
                "name": "Abidjan Vridi Industrial 225kV Substation Upgrade",
                "anchors_served": ["AL_ANC_003", "AL_ANC_004", "AL_ANC_005"],
                "voltage_kv": 225,
                "configuration": "New 225/11kV industrial substation at Vridi zone center",
                "length_km": 6.0,
                "capacity_mw": 180.0,
                "security_standard": "N-1",
                "conductor_type": "XLPE 400mm² underground in port and zone area",
                "rationale": (
                    "New dedicated industrial substation separates port, "
                    "ZIEX, and cocoa processing from residential CIE distribution network. "
                    "225kV interface with Abidjan 225kV ring allows both "
                    "Azito and CIPREL to supply the industrial zone independently."
                ),
            },

            {
                "segment_id": "SEG_DR_004",
                "gap_id": "GAP_010",
                "phase": "Phase 2",
                "name": "Sagamu Interchange 132kV Substation Capacity Upgrade",
                "anchors_served": ["AL_ANC_032"],
                "voltage_kv": 132,
                "configuration": "Existing substation transformer replacement: 40 MVA → 2×60 MVA",
                "length_km": 0.0,
                "capacity_mw": 100.0,
                "security_standard": "N-1",
                "conductor_type": "N/A — substation upgrade only",
                "rationale": (
                    "Existing 132kV Sagamu substation at 95% capacity. "
                    "Transformer replacement from 1×40 MVA to 2×60 MVA provides "
                    "N-1 redundancy (one transformer out = other covers full load) "
                    "and doubles available capacity to 100 MW. "
                    "No new line construction required — substation upgrade only. "
                    "Lowest cost intervention on the corridor at $28M."
                ),
            },
        ],

        # ================================================================
        # LEKKI HUB — Special engineering specification
        # The most complex single asset on the corridor
        # ================================================================
        "lekki_hub_specification": {
            "hub_id": "HUB_LEKKI_001",
            "gap_id": "GAP_003",
            "phase": "Phase 1",
            "name": "Lekki 400kV Transmission Hub",
            "location": "Lekki Peninsula, Lagos State, Nigeria",
            "coords": {"latitude": 6.435, "longitude": 3.820},
            "anchors_directly_served": [
                "AL_ANC_027",  # Dangote Refinery (1,000 MW)
                "AL_ANC_028",  # Lekki FTZ (150 MW → 1,200 MW)
                "AL_ANC_029",  # Lekki Deep Sea Port (35 MW)
                "AL_ANC_030",  # MainOne Data Center (18 MW)
            ],
            "hub_configuration": {
                "voltage_levels": ["400kV", "330kV", "132kV"],
                "transformer_bays": {
                    "400_330kv": "2 × 800 MVA autotransformers (N-1 redundancy)",
                    "330_132kv": "4 × 200 MVA transformers (N-1-1 for Dangote feeds)",
                },
                "incoming_circuits": [
                    "SEG_BB_005 Circuit 1 — 400kV from Maria Gleta (Cotonou)",
                    "SEG_BB_005 Circuit 2 — 400kV from Maria Gleta (Cotonou, separate route)",
                    "Future: 400kV from Omotosho (for N-1-1 diversified supply)",
                ],
                "outgoing_feeders": [
                    "Dangote Refinery: 2 × 330kV dedicated feeders (N-1-1)",
                    "Lekki FTZ: 1 × 330kV feeder Phase 1, upgrade to 2 circuits Year 5",
                    "Lekki Deep Sea Port: 1 × 132kV feeder",
                    "MainOne DC: 2 × 132kV feeders (N-1-1 for Tier III/IV SLA)",
                    "Future Lekki FTZ expansion: 2 × 330kV feeders Year 5–8",
                ],
                "phase_1a_capacity_mw": 500.0,
                "phase_1b_capacity_mw": 2500.0,
                "ultimate_capacity_mw": 4500.0,
            },
            "rationale": (
                "The Lekki hub is the most complex and highest-value asset on the corridor. "
                "It must serve 1,000 MW (Dangote) with N-1-1 security on Day 1, "
                "while providing a platform to grow to 4,500 MW over 20 years "
                "as Lekki FTZ reaches full buildout. "
                "The hub design separates Dangote's Critical feeds from FTZ feeds — "
                "a fault on the FTZ feeder cannot interrupt refinery supply. "
                "Phase 1A ($145M) delivers 500 MW capacity immediately. "
                "Phase 1B ($235M) adds 2,000 MW capacity by Year 5 "
                "aligned with Lekki FTZ buildout milestones."
            ),
        },

        # ================================================================
        # CORRIDOR SUMMARY
        # ================================================================
        "corridor_summary": {
            "total_segments": 12,
            "backbone_segments": 5,
            "spur_segments": 3,
            "distribution_reinforcements": 4,

            "voltage_mix": {
                "400kv_km": 152.0,    # SEG_BB_005 — Cotonou to Lekki (highest demand)
                "330kv_km": 937.0,    # SEG_BB_001 through SEG_BB_004
                "161kv_km": 195.0,    # Obuasi, Volta, Lithium spurs
                "33_132kv_km": 32.0,  # Distribution reinforcements
                "total_line_km": 1316.0,
            },

            "conductor_mix": {
                "ACCC_quad_bundle_km": 152.0,   # Highest demand segment (400kV Lagos)
                "AAAC_twin_bundle_km": 937.0,   # Coastal backbone (330kV)
                "ACSR_various_km": 177.0,        # Inland spurs (161kV)
                "XLPE_underground_km": 50.0,     # Urban sections, port areas
            },

            "security_standards": {
                "N-1-1_segments": [
                    "SEG_BB_002 (Takoradi–Tema — Critical Tema anchors)",
                    "SEG_BB_005 (Cotonou–Lekki — Critical Dangote/Lekki)",
                    "SEG_SP_001 (Obuasi spur — Critical underground mine)",
                ],
                "N-1_segments": [
                    "SEG_BB_001", "SEG_BB_003", "SEG_BB_004",
                    "SEG_SP_003 (when built)",
                    "All distribution reinforcements",
                ],
                "N-0_segments": [
                    "SEG_SP_002 (Volta agri spur — Standard reliability class)",
                ],
            },

            "total_estimated_line_losses": {
                "400kv_segment_pct": 0.9,
                "330kv_backbone_avg_pct": 2.1,
                "161kv_spurs_avg_pct": 2.4,
                "weighted_corridor_avg_pct": 1.8,
                "note": (
                    "Weighted average 1.8% corridor losses vs typical West Africa "
                    "grid losses of 18–25% (distribution included). "
                    "Transmission-only losses of 1.8% are industry-standard "
                    "for a new high-voltage backbone."
                ),
            },

            "reactive_power_compensation_sites": 8,
            "border_crossings": 4,
            "underground_cable_sections_km": 50.0,
            "protected_area_deviations": 3,
        },

        "message": (
            "Voltage and capacity sizing complete for all 12 corridor segments. "
            "Corridor uses 400kV for the Cotonou–Lekki segment (1,293 MW current demand), "
            "330kV for all four coastal backbone segments (105–200 MW), "
            "and 161kV for mining and agricultural spurs. "
            "Weighted average line losses: 1.8% — well within international standards. "
            "Lekki 400kV hub sized for 500 MW Phase 1A, upgradeable to 4,500 MW. "
            "N-1-1 security applied to all Critical-class anchor segments. "
            "Total transmission line construction: 1,316 km across 12 segments."
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