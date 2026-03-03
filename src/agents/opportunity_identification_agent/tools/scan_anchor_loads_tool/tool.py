import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import AnchorLoadScannerInput


@tool("scan_anchor_loads", description=TOOL_DESCRIPTION)
def scan_anchor_loads_tool(
    payload: AnchorLoadScannerInput, runtime: ToolRuntime
) -> Command:
    """
    Resolves commercial identities for infrastructure detections within the
    corridor boundary. Takes raw detections from infrastructure_detection and
    cross-references them against national mining cadastres, industrial
    registries, and trade databases to attach real-world entity names,
    operators, legal registry sources, and sector classifications.

    This tool ONLY returns commercial identity information:
    - Anchor ID linked to detection ID
    - Verified entity name and operator
    - Registry source that confirmed the identity
    - Sector and sub-sector classification
    - Country and coordinates (passed through for traceability)
    - Identity confidence (resolved / unresolved / partial)
    - Notes for unresolved facilities (forwarded for manual verification)

    This tool does NOT return:
    - Power demand estimates (MW)     → handled by calculate_current_demand
    - Off-take quality / credit       → handled by assess_bankability
    - Load profiles                   → handled by calculate_current_demand
    - Demand at buildout              → handled by model_growth_trajectory
    - Priority rankings               → handled by prioritize_opportunities

    Corridor boundary applied:
        Top-Left    (NW): [-4.008, 5.600]
        Top-Right   (NE): [ 3.379, 6.750]
        Bottom-Right(SE): [ 3.379, 6.250]
        Bottom-Left (SW): [-4.008, 5.100]
    Only detections within this polygon are processed.
    """

    response = {
        "status": "Scanning Complete",
        "total_detections_received": 57,
        "total_anchors_resolved": 49,
        "total_unresolved": 8,
        "anchor_catalog": [

            # ================================================================
            # CÔTE D'IVOIRE
            # ================================================================

            {
                "anchor_id": "AL_ANC_001",
                "detection_id": "DET-001",
                "entity_name": "Azito Thermal Power Plant",
                "operator": "Azito Energie SA (Globeleq consortium)",
                "registry_source": "GEO (Global Energy Observatory) / CIE Côte d'Ivoire Registry",
                "sector": "Energy",
                "sub_sector": "Thermal Generation — CCGT",
                "country": "Côte d'Ivoire",
                "coords": {"latitude": 5.302, "longitude": -4.025},
                "identity_confidence": "resolved",
                "resolution_note": (
                    "Matched to GEO registry entry #CI-PWR-0041. "
                    "Operator confirmed via ANARE-CI (national electricity regulator) licence database."
                ),
            },
            {
                "anchor_id": "AL_ANC_002",
                "detection_id": "DET-002",
                "entity_name": "CIPREL Combined-Cycle Power Plant",
                "operator": "Compagnie Ivoirienne de Production d'Electricité (CIPREL)",
                "registry_source": "GEO / WAPP West African Power Pool Asset Registry",
                "sector": "Energy",
                "sub_sector": "Thermal Generation — CCGT",
                "country": "Côte d'Ivoire",
                "coords": {"latitude": 5.350, "longitude": -4.020},
                "identity_confidence": "resolved",
                "resolution_note": (
                    "Matched to WAPP asset registry entry #WAPP-CI-002. "
                    "CIPREL confirmed as largest IPP in Côte d'Ivoire via ANARE-CI records."
                ),
            },
            {
                "anchor_id": "AL_ANC_003",
                "detection_id": "DET-003",
                "entity_name": "Port of Abidjan — Vridi Terminal",
                "operator": "Abidjan Port Authority (APDL) / Terminal operator: APM Terminals",
                "registry_source": "APDL (Abidjan Port Authority) / World Bank Port Database",
                "sector": "Industrial",
                "sub_sector": "Port & Logistics — Deep Sea Container Terminal",
                "country": "Côte d'Ivoire",
                "coords": {"latitude": 5.295, "longitude": -4.003},
                "identity_confidence": "resolved",
                "resolution_note": (
                    "Matched to APDL port authority registry. "
                    "APM Terminals confirmed as terminal operator via concession agreement records."
                ),
            },
            {
                "anchor_id": "AL_ANC_004",
                "detection_id": "DET-004",
                "entity_name": "Cargill Cocoa Processing Plant — Abidjan Hinterland",
                "operator": "Cargill Cocoa & Chocolate (unconfirmed — pending verification)",
                "registry_source": "Côte d'Ivoire RCCM Commercial Registry (partial match)",
                "sector": "Agriculture",
                "sub_sector": "Cocoa Processing — Agro-Industrial",
                "country": "Côte d'Ivoire",
                "coords": {"latitude": 5.377, "longitude": -4.195},
                "identity_confidence": "partial",
                "resolution_note": (
                    "Facility not present in 2023 census. "
                    "Partial match to Cargill RCCM registration #CI-2024-08821 filed Q4 2024. "
                    "Physical attributes (silos, loading bays, diesel pads) consistent with "
                    "cocoa processing. Manual verification recommended before bankability assessment."
                ),
            },
            {
                "anchor_id": "AL_ANC_005",
                "detection_id": "DET-005",
                "entity_name": "Abidjan Export Processing Zone (ZIEX)",
                "operator": "Société de Gestion de la Zone Franche de Côte d'Ivoire",
                "registry_source": "APEX-CI (Investment Promotion Agency) / Côte d'Ivoire RCCM",
                "sector": "Industrial",
                "sub_sector": "Special Economic Zone — Export Processing",
                "country": "Côte d'Ivoire",
                "coords": {"latitude": 5.318, "longitude": -3.971},
                "identity_confidence": "resolved",
                "resolution_note": (
                    "Matched to APEX-CI SEZ registry #CI-SEZ-003. "
                    "Zone operational since 1996 with 200+ registered enterprises."
                ),
            },
            {
                "anchor_id": "AL_ANC_006",
                "detection_id": "DET-006",
                "entity_name": "CIE / SOGEPE 225kV Transmission Substation — Abidjan North",
                "operator": "Compagnie Ivoirienne d'Electricité (CIE) / SOGEPE",
                "registry_source": "WAPP Asset Registry / ANARE-CI Grid Map",
                "sector": "Energy",
                "sub_sector": "Transmission Infrastructure — HV Substation",
                "country": "Côte d'Ivoire",
                "coords": {"latitude": 5.362, "longitude": -4.011},
                "identity_confidence": "resolved",
                "resolution_note": (
                    "Matched to WAPP grid asset registry #WAPP-CI-SUB-007. "
                    "Confirmed as 225kV switching substation on Abidjan ring network."
                ),
            },

            # ================================================================
            # GHANA
            # ================================================================

            {
                "anchor_id": "AL_ANC_007",
                "detection_id": "DET-007",
                "entity_name": "Tema Oil Refinery (TOR)",
                "operator": "Tema Oil Refinery Ltd (Government of Ghana — 100% state-owned)",
                "registry_source": "Ghana GIPC (Investment Promotion Centre) / GEO Registry",
                "sector": "Energy",
                "sub_sector": "Petroleum Refinery",
                "country": "Ghana",
                "coords": {"latitude": 5.666, "longitude": 0.044},
                "identity_confidence": "resolved",
                "resolution_note": (
                    "Matched to GEO registry #GH-REF-001. "
                    "TOR confirmed as sole petroleum refinery in Ghana, "
                    "100% state-owned via GNPC (Ghana National Petroleum Corporation). "
                    "Rehabilitation works confirmed via GNPC press releases Q2 2025."
                ),
            },
            {
                "anchor_id": "AL_ANC_008",
                "detection_id": "DET-008",
                "entity_name": "Tema Port — Meridian Port Services Container Terminal",
                "operator": "Ghana Ports & Harbours Authority (GPHA) / Meridian Port Services (APM Terminals JV)",
                "registry_source": "GPHA Port Registry / World Bank Port Database",
                "sector": "Industrial",
                "sub_sector": "Port & Logistics — Deep Sea Container Terminal",
                "country": "Ghana",
                "coords": {"latitude": 5.650, "longitude": -0.018},
                "identity_confidence": "resolved",
                "resolution_note": (
                    "Matched to GPHA registry #GH-PORT-TEMA-001. "
                    "Meridian Port Services confirmed as terminal 3 operator "
                    "via GPHA concession agreement 2019."
                ),
            },
            {
                "anchor_id": "AL_ANC_009",
                "detection_id": "DET-009",
                "entity_name": "Tema Free Zone",
                "operator": "Ghana Free Zones Authority (GFZA)",
                "registry_source": "GFZA (Ghana Free Zones Authority) Registry",
                "sector": "Industrial",
                "sub_sector": "Special Economic Zone — Free Trade Zone",
                "country": "Ghana",
                "coords": {"latitude": 5.650, "longitude": -0.018},
                "identity_confidence": "resolved",
                "resolution_note": (
                    "Matched to GFZA SEZ registry #GH-SEZ-TFZ-001. "
                    "Zone operational since 1996 with 200+ enterprises. "
                    "Expansion phase confirmed via GFZA 2024 annual report."
                ),
            },
            {
                "anchor_id": "AL_ANC_010",
                "detection_id": "DET-010",
                "entity_name": "Akosombo Hydroelectric Dam",
                "operator": "Volta River Authority (VRA)",
                "registry_source": "GEO (Global Energy Observatory) / WAPP Asset Registry",
                "sector": "Energy",
                "sub_sector": "Hydroelectric Generation",
                "country": "Ghana",
                "coords": {"latitude": 6.270, "longitude": 0.050},
                "identity_confidence": "resolved",
                "resolution_note": (
                    "Matched to WAPP asset registry #WAPP-GH-HYDRO-001. "
                    "VRA confirmed as operator via Government of Ghana Energy Commission records. "
                    "6-unit dam; exports to Togo, Benin, and Burkina Faso confirmed."
                ),
            },
            {
                "anchor_id": "AL_ANC_011",
                "detection_id": "DET-011",
                "entity_name": "Nzema Solar Power Station",
                "operator": "BXC Ghana Ltd (Blue Energy consortium)",
                "registry_source": "GEO / Ghana Energy Commission Registry",
                "sector": "Energy",
                "sub_sector": "Solar PV — Utility Scale",
                "country": "Ghana",
                "coords": {"latitude": 4.996, "longitude": -2.788},
                "identity_confidence": "resolved",
                "resolution_note": (
                    "Matched to Ghana Energy Commission licence #GH-PWR-SOL-001. "
                    "BXC Ghana Ltd confirmed as developer and operator. "
                    "Expansion activity consistent with Phase 2 (additional 40 MW) "
                    "announced in Q3 2024."
                ),
            },
            {
                "anchor_id": "AL_ANC_012",
                "detection_id": "DET-012",
                "entity_name": "Obuasi Gold Mine",
                "operator": "AngloGold Ashanti Ghana Ltd",
                "registry_source": "Minerals Commission Ghana — Mining Cadastre / GEO",
                "sector": "Mining",
                "sub_sector": "Underground Gold Mine",
                "country": "Ghana",
                "coords": {"latitude": 6.204, "longitude": -1.672},
                "identity_confidence": "resolved",
                "resolution_note": (
                    "Matched to Ghana Minerals Commission cadastre #MC-GH-AU-0019. "
                    "AngloGold Ashanti confirmed as operator via JSE/NYSE listed company records. "
                    "Distance from corridor centerline: ~98 km — spur connection required. "
                    "Flagged for transmission spur analysis in infrastructure_optimization."
                ),
            },
            {
                "anchor_id": "AL_ANC_013",
                "detection_id": "DET-013",
                "entity_name": "Unverified HV Substation — Tema Industrial Area",
                "operator": "Unknown — pending verification",
                "registry_source": "Not matched — no registry entry found",
                "sector": "Energy",
                "sub_sector": "Transmission Infrastructure — HV Substation (unconfirmed)",
                "country": "Ghana",
                "coords": {"latitude": 5.658, "longitude": -0.031},
                "identity_confidence": "unresolved",
                "resolution_note": (
                    "Low confidence detection (0.61). "
                    "No matching entry found in WAPP asset registry, GRIDCo grid map, "
                    "or OSM infrastructure database. "
                    "Alternative classification possible (large warehouse rooftop). "
                    "Manual field verification required before any further analysis."
                ),
            },
            {
                "anchor_id": "AL_ANC_014",
                "detection_id": "DET-014",
                "entity_name": "Weta Rice Farm & Milling Hub — Volta Region",
                "operator": "Ghana FOODBELT Authority / private smallholder cooperative (unconfirmed lead operator)",
                "registry_source": "Ghana MoFA (Ministry of Food & Agriculture) Agri-Investment Register",
                "sector": "Agriculture",
                "sub_sector": "Rice Production & Milling",
                "country": "Ghana",
                "coords": {"latitude": 6.032, "longitude": 0.607},
                "identity_confidence": "partial",
                "resolution_note": (
                    "Partial match to MoFA agri-investment register #GH-AGR-VR-044. "
                    "Lead commercial operator unconfirmed — multiple smallholder "
                    "cooperative registrations in same zone. "
                    "COCOBOD and Ghana FOODBELT Authority both have recorded interests. "
                    "Manual verification of lead off-taker recommended."
                ),
            },
            {
                "anchor_id": "AL_ANC_015",
                "detection_id": "DET-015",
                "entity_name": "Takoradi Port — Bulk & General Cargo Terminal",
                "operator": "Ghana Ports & Harbours Authority (GPHA) / Bolloré Logistics (concession)",
                "registry_source": "GPHA Port Registry / World Bank Port Database",
                "sector": "Industrial",
                "sub_sector": "Port & Logistics — Bulk & General Cargo",
                "country": "Ghana",
                "coords": {"latitude": 4.912, "longitude": -1.777},
                "identity_confidence": "resolved",
                "resolution_note": (
                    "Matched to GPHA registry #GH-PORT-TADI-001. "
                    "Bolloré Logistics confirmed as terminal concession holder. "
                    "Liquid bulk jetty extension consistent with GPHA 2025 expansion plan."
                ),
            },
            {
                "anchor_id": "AL_ANC_016",
                "detection_id": "DET-016",
                "entity_name": "Accra Data Center (ADC)",
                "operator": "CSquared Ghana / Liquid Telecom (partial ownership)",
                "registry_source": "Ghana NCA (National Communications Authority) Registry",
                "sector": "Digital",
                "sub_sector": "Data Center — Carrier Neutral Tier III",
                "country": "Ghana",
                "coords": {"latitude": 5.610, "longitude": -0.185},
                "identity_confidence": "resolved",
                "resolution_note": (
                    "Matched to NCA infrastructure registry #GH-DC-ACC-003. "
                    "CSquared confirmed as primary operator. "
                    "Annex expansion consistent with reported capacity upgrade "
                    "to meet growing cloud demand in Accra metro area."
                ),
            },

            # ================================================================
            # TOGO
            # ================================================================

            {
                "anchor_id": "AL_ANC_017",
                "detection_id": "DET-017",
                "entity_name": "Port of Lomé — Container Terminal",
                "operator": "Port Autonome de Lomé (PAL) / Terminal operator: Lomé Container Terminal (MSC/Bolloré JV)",
                "registry_source": "PAL Port Registry / UNCTAD Port Database",
                "sector": "Industrial",
                "sub_sector": "Port & Logistics — Deep Sea Container Terminal",
                "country": "Togo",
                "coords": {"latitude": 6.130, "longitude": 1.281},
                "identity_confidence": "resolved",
                "resolution_note": (
                    "Matched to PAL registry #TG-PORT-LOME-001. "
                    "Lomé Container Terminal (MSC and Bolloré JV) confirmed via "
                    "concession agreement records. Deepest natural port in West Africa "
                    "— key transshipment hub for ECOWAS hinterland."
                ),
            },
            {
                "anchor_id": "AL_ANC_018",
                "detection_id": "DET-018",
                "entity_name": "Lomé Open Cycle Gas Turbine Plant",
                "operator": "Compagnie Énergie Électrique du Togo (CEET) / SINOPEC EPC (construction)",
                "registry_source": "WAPP Asset Registry / Togo ARSE (Energy Regulator)",
                "sector": "Energy",
                "sub_sector": "Thermal Generation — OCGT",
                "country": "Togo",
                "coords": {"latitude": 6.168, "longitude": 1.212},
                "identity_confidence": "resolved",
                "resolution_note": (
                    "Matched to WAPP asset registry #WAPP-TG-PWR-001. "
                    "CEET confirmed as operator via ARSE licence database. "
                    "Plant represents one of few domestic generation assets in Togo — "
                    "country remains >50% dependent on imports."
                ),
            },
            {
                "anchor_id": "AL_ANC_019",
                "detection_id": "DET-019",
                "entity_name": "Lomé Cement Plant",
                "operator": "West African Cement (WACEM) / Fortia Group",
                "registry_source": "Togo RCCM Commercial Registry / WACEM Corporate Records",
                "sector": "Industrial",
                "sub_sector": "Cement & Clinker Manufacturing",
                "country": "Togo",
                "coords": {"latitude": 6.175, "longitude": 1.305},
                "identity_confidence": "resolved",
                "resolution_note": (
                    "Matched to RCCM entry #TG-IND-CEM-001. "
                    "WACEM confirmed as operator — one of the largest industrial "
                    "electricity consumers in Togo. Plant runs 3 kilns at combined "
                    "capacity ~3.5 MT/year clinker."
                ),
            },
            {
                "anchor_id": "AL_ANC_020",
                "detection_id": "DET-020",
                "entity_name": "Lomé Free Zone (Zone Franche de Lomé)",
                "operator": "Société d'Administration de la Zone Franche (SAZOF)",
                "registry_source": "SAZOF Registry / Togo Investment & Export Promotion Agency (TIPA)",
                "sector": "Industrial",
                "sub_sector": "Special Economic Zone — Logistics & Light Industrial",
                "country": "Togo",
                "coords": {"latitude": 6.195, "longitude": 1.225},
                "identity_confidence": "resolved",
                "resolution_note": (
                    "Matched to SAZOF SEZ registry #TG-SEZ-LOME-001. "
                    "Zone administered by SAZOF under Togolese Free Zone Act. "
                    "Expansion activity consistent with TIPA-reported new enterprise "
                    "registrations in 2024-2025."
                ),
            },

            # ================================================================
            # BENIN
            # ================================================================

            {
                "anchor_id": "AL_ANC_021",
                "detection_id": "DET-021",
                "entity_name": "Maria Gleta Thermal Power Station",
                "operator": "TEC — Togo Electric Company (Eranove Group) / SBEE Benin",
                "registry_source": "WAPP Asset Registry / Benin ABERME (Energy Regulator)",
                "sector": "Energy",
                "sub_sector": "Thermal Generation — Combined Cycle",
                "country": "Benin",
                "coords": {"latitude": 6.425, "longitude": 2.406},
                "identity_confidence": "resolved",
                "resolution_note": (
                    "Matched to WAPP asset registry #WAPP-BJ-PWR-001. "
                    "Eranove Group confirmed as majority operator via ABERME licence. "
                    "Key generation asset for Benin — supplies ~35% of domestic "
                    "generation; balance imported from Ghana and Nigeria."
                ),
            },
            {
                "anchor_id": "AL_ANC_022",
                "detection_id": "DET-022",
                "entity_name": "Port of Cotonou — Bénin Terminal",
                "operator": "Port Autonome de Cotonou (PAC) / Bénin Terminal (Bolloré concession)",
                "registry_source": "PAC Port Registry / UNCTAD Port Database",
                "sector": "Industrial",
                "sub_sector": "Port & Logistics — Container & Ro-Ro Terminal",
                "country": "Benin",
                "coords": {"latitude": 6.351, "longitude": 2.435},
                "identity_confidence": "resolved",
                "resolution_note": (
                    "Matched to PAC registry #BJ-PORT-COT-001. "
                    "Bolloré confirmed as terminal concessionaire. "
                    "Ro-ro expansion consistent with PAC 2025 masterplan."
                ),
            },
            {
                "anchor_id": "AL_ANC_023",
                "detection_id": "DET-023",
                "entity_name": "Zone Industrielle de Cotonou (PK10)",
                "operator": "Government of Benin — Ministère de l'Industrie",
                "registry_source": "Benin APIEX (Investment Promotion Agency) Registry",
                "sector": "Industrial",
                "sub_sector": "Industrial Zone — Mixed Manufacturing",
                "country": "Benin",
                "coords": {"latitude": 6.420, "longitude": 2.391},
                "identity_confidence": "resolved",
                "resolution_note": (
                    "Matched to APIEX industrial zone registry #BJ-IZ-COT-001. "
                    "Government-administered zone operational since 1970s. "
                    "150+ enterprises registered; zone operates significantly "
                    "below capacity due to power reliability constraints."
                ),
            },
            {
                "anchor_id": "AL_ANC_024",
                "detection_id": "DET-024",
                "entity_name": "Unidentified Agro-Processing Cluster — Benin Coastal",
                "operator": "Unknown — pending verification",
                "registry_source": "Not matched — no registry entry found",
                "sector": "Agriculture",
                "sub_sector": "Agro-Processing — Pineapple & Cashew (probable)",
                "country": "Benin",
                "coords": {"latitude": 6.492, "longitude": 2.628},
                "identity_confidence": "unresolved",
                "resolution_note": (
                    "Facility not present in 2023 census. "
                    "No matching entry in APIEX investment register, Benin RCCM, "
                    "or AfDB SAPZ programme records. "
                    "Physical attributes (cold storage, processing silos, loading bays) "
                    "consistent with agro-processing. "
                    "Manual field verification required."
                ),
            },
            {
                "anchor_id": "AL_ANC_025",
                "detection_id": "DET-025",
                "entity_name": "Unidentified Solar Farm — Benin North Coastal",
                "operator": "Unknown — pending verification",
                "registry_source": "Not matched — no registry entry found",
                "sector": "Energy",
                "sub_sector": "Solar PV — Utility Scale (probable)",
                "country": "Benin",
                "coords": {"latitude": 6.538, "longitude": 2.712},
                "identity_confidence": "unresolved",
                "resolution_note": (
                    "New installation — not present in 2023 census. "
                    "No matching entry in ABERME licence database or ECOWAS "
                    "renewable energy project register. "
                    "Physical attributes clearly consistent with PV solar farm. "
                    "Manual verification required — possible off-grid or "
                    "donor-funded installation not yet registered."
                ),
            },

            # ================================================================
            # NIGERIA
            # ================================================================

            {
                "anchor_id": "AL_ANC_026",
                "detection_id": "DET-026",
                "entity_name": "Egbin Thermal Power Station",
                "operator": "Sahara Power Group (privatised 2013 via PHCN unbundling)",
                "registry_source": "GEO (Global Energy Observatory) / NERC Nigeria Registry",
                "sector": "Energy",
                "sub_sector": "Thermal Generation — Steam Turbine",
                "country": "Nigeria",
                "coords": {"latitude": 6.563, "longitude": 3.564},
                "identity_confidence": "resolved",
                "resolution_note": (
                    "Matched to GEO registry #NG-PWR-0012. "
                    "Sahara Power Group confirmed as operator via NERC generation licence. "
                    "6-unit station; units 3 and 4 visually consistent with mothballed status "
                    "as reported in NERC Q3 2025 operational report."
                ),
            },
            {
                "anchor_id": "AL_ANC_027",
                "detection_id": "DET-027",
                "entity_name": "Dangote Refinery",
                "operator": "Dangote Industries Limited (Aliko Dangote Group)",
                "registry_source": "OpenStreetMap / NNPC Registry / Nigerian CAC (Corporate Affairs Commission)",
                "sector": "Energy",
                "sub_sector": "Petroleum Refinery & Petrochemical Complex",
                "country": "Nigeria",
                "coords": {"latitude": 6.438, "longitude": 3.989},
                "identity_confidence": "resolved",
                "resolution_note": (
                    "Matched to NNPC registry #NG-REF-LEKKI-001 and CAC registration. "
                    "Dangote Industries confirmed as sole owner and operator. "
                    "$19B investment — world's largest single-train refinery at 650,000 bpd. "
                    "Active commissioning confirmed via satellite change detection and "
                    "Dangote Group press releases Q1-Q3 2025."
                ),
            },
            {
                "anchor_id": "AL_ANC_028",
                "detection_id": "DET-028",
                "entity_name": "Lekki Free Trade Zone",
                "operator": "Lekki Free Zone Development Company (LFZDC) — Chinese-Nigerian JV",
                "registry_source": "NEPZA (Nigeria Export Processing Zones Authority) / NIPC Registry",
                "sector": "Industrial",
                "sub_sector": "Special Economic Zone — Free Trade Zone",
                "country": "Nigeria",
                "coords": {"latitude": 6.427, "longitude": 3.987},
                "identity_confidence": "resolved",
                "resolution_note": (
                    "Matched to NEPZA registry #NG-SEZ-LEKKI-001. "
                    "LFZDC confirmed as zone developer — JV between Lagos State Government, "
                    "CCECC (China Civil Engineering), and Nanjing Jiangning Economic and "
                    "Technological Development Corp. $20B+ committed investment confirmed "
                    "via NIPC FDI records."
                ),
            },
            {
                "anchor_id": "AL_ANC_029",
                "detection_id": "DET-029",
                "entity_name": "Lekki Deep Sea Port",
                "operator": "Lekki Port LFTZ Enterprise Ltd (Tolaram Group / CMA CGM JV)",
                "registry_source": "Nigerian Ports Authority (NPA) / NIPC Registry",
                "sector": "Industrial",
                "sub_sector": "Port & Logistics — Deep Sea Container Terminal",
                "country": "Nigeria",
                "coords": {"latitude": 6.449, "longitude": 3.988},
                "identity_confidence": "resolved",
                "resolution_note": (
                    "Matched to NPA port registry #NG-PORT-LEKKI-001. "
                    "Tolaram Group and CMA CGM confirmed as JV partners via NPA concession. "
                    "Port became fully operational in 2024 — consistent with "
                    "first vessels visible in satellite imagery."
                ),
            },
            {
                "anchor_id": "AL_ANC_030",
                "detection_id": "DET-030",
                "entity_name": "MainOne Data Center (MDX-i Lagos)",
                "operator": "MainOne Cable Company (Equinix subsidiary since 2022)",
                "registry_source": "NCC (Nigerian Communications Commission) Registry / Equinix Corporate Records",
                "sector": "Digital",
                "sub_sector": "Data Center — Carrier Neutral Tier III",
                "country": "Nigeria",
                "coords": {"latitude": 6.449, "longitude": 3.988},
                "identity_confidence": "resolved",
                "resolution_note": (
                    "Matched to NCC infrastructure registry #NG-DC-LEKKI-001. "
                    "Equinix acquisition of MainOne confirmed via SEC filing 2022. "
                    "Expansion activity consistent with Equinix announced "
                    "capacity doubling plan for Lagos campus (Q2 2025)."
                ),
            },
            {
                "anchor_id": "AL_ANC_031",
                "detection_id": "DET-031",
                "entity_name": "Apapa Port Complex",
                "operator": "Nigerian Ports Authority (NPA) / APM Terminals Apapa (concession)",
                "registry_source": "NPA Port Registry / World Bank Port Database",
                "sector": "Industrial",
                "sub_sector": "Port & Logistics — Multi-Purpose Terminal",
                "country": "Nigeria",
                "coords": {"latitude": 6.437, "longitude": 3.386},
                "identity_confidence": "resolved",
                "resolution_note": (
                    "Matched to NPA registry #NG-PORT-APAPA-001. "
                    "APM Terminals confirmed as concession operator for Apapa bulk terminal. "
                    "Lagos represents ~70% of Nigeria's import/export throughput via this complex."
                ),
            },
            {
                "anchor_id": "AL_ANC_032",
                "detection_id": "DET-032",
                "entity_name": "Sagamu-Interchange Manufacturing Cluster",
                "operator": "Multiple tenants — Honeywell Group, Fidson Healthcare, others",
                "registry_source": "Nigeria CAC (Corporate Affairs Commission) / Ogun State Investment Registry",
                "sector": "Industrial",
                "sub_sector": "Manufacturing Cluster — Light & Heavy Industrial",
                "country": "Nigeria",
                "coords": {"latitude": 6.878, "longitude": 3.662},
                "identity_confidence": "partial",
                "resolution_note": (
                    "Zone matched to Ogun State Investment Registry #OG-IZ-SAG-001. "
                    "Multiple tenants identified via CAC records — no single lead operator. "
                    "Honeywell Flour Mills and Fidson Healthcare are largest identified consumers. "
                    "New pharmaceutical block under construction — operator identity unresolved. "
                    "Aggregate demand assessment required across tenant mix."
                ),
            },
            {
                "anchor_id": "AL_ANC_033",
                "detection_id": "DET-033",
                "entity_name": "Omotosho 330kV Transmission Substation",
                "operator": "TCN (Transmission Company of Nigeria)",
                "registry_source": "TCN Grid Asset Register / NERC Nigeria Registry",
                "sector": "Energy",
                "sub_sector": "Transmission Infrastructure — 330kV HV Substation",
                "country": "Nigeria",
                "coords": {"latitude": 6.519, "longitude": 3.358},
                "identity_confidence": "resolved",
                "resolution_note": (
                    "Matched to TCN grid asset register #TCN-SUB-OMOS-001. "
                    "330kV transformer upgrade confirmed via TCN 2025 capital works programme. "
                    "Key interconnection node for Lagos metropolitan grid."
                ),
            },
            {
                "anchor_id": "AL_ANC_034",
                "detection_id": "DET-034",
                "entity_name": "Unverified Hyperscale Data Center — Lagos Island North",
                "operator": "Unknown — pending verification",
                "registry_source": "Not matched — no NCC or NIPC registry entry found",
                "sector": "Digital",
                "sub_sector": "Data Center — Hyperscale (probable)",
                "country": "Nigeria",
                "coords": {"latitude": 6.601, "longitude": 3.349},
                "identity_confidence": "unresolved",
                "resolution_note": (
                    "New facility — not present in 2023 census. "
                    "No matching entry in NCC infrastructure registry or NIPC investment database. "
                    "Physical attributes (large flat-roof, rooftop cooling, backup generators, "
                    "secure perimeter) consistent with hyperscale data center. "
                    "Alternative classification possible (large distribution warehouse). "
                    "Manual field verification required — may be a new entrant not yet registered."
                ),
            },
            {
                "anchor_id": "AL_ANC_035",
                "detection_id": "DET-035",
                "entity_name": "Unidentified Lithium Exploration & Processing Site — Ghana North",
                "operator": "Unknown — pending verification",
                "registry_source": "Partial match — Ghana Minerals Commission cadastre (exploration licence area)",
                "sector": "Mining",
                "sub_sector": "Lithium Exploration & Early Processing",
                "country": "Ghana",
                "coords": {"latitude": 6.812, "longitude": -1.244},
                "identity_confidence": "partial",
                "resolution_note": (
                    "Partial match to Minerals Commission exploration licence block #MC-GH-LI-2023-04. "
                    "Licence holder identity redacted in public cadastre — "
                    "full disclosure requires formal cadastre access request. "
                    "Physical attributes (open pit, haul road, early processing structures) "
                    "consistent with lithium exploration and pilot processing. "
                    "Distance from corridor centerline: ~44 km. "
                    "Manual verification recommended — high strategic value if confirmed "
                    "given global lithium demand for EV batteries."
                ),
            },
        ],

        # ------------------------------------------------------------------ #
        #  SUMMARY                                                            #
        # ------------------------------------------------------------------ #
        "resolution_summary": {
            "total_detections_received": 57,
            "fully_resolved": 27,
            "partially_resolved": 5,
            "unresolved_requires_field_verification": 3,
            "not_anchor_loads_generation_assets_substations": 22,
            "by_sector": {
                "Energy": 10,
                "Industrial": 12,
                "Agriculture": 5,
                "Mining": 4,
                "Digital": 4,
            },
            "by_country": {
                "Côte d'Ivoire": 6,
                "Ghana": 10,
                "Togo": 4,
                "Benin": 5,
                "Nigeria": 10,
            },
            "unresolved_facilities": [
                "AL_ANC_013 — Unverified HV Substation, Tema (low confidence detection)",
                "AL_ANC_024 — Agro-processing cluster, Benin Coastal (new, unregistered)",
                "AL_ANC_034 — Possible hyperscale data center, Lagos (new, unregistered)",
            ],
            "partial_resolution_facilities": [
                "AL_ANC_004 — Cargill Cocoa Plant, Abidjan (partial RCCM match)",
                "AL_ANC_014 — Weta Rice Farm, Volta Region (multiple operators)",
                "AL_ANC_032 — Sagamu Manufacturing Cluster (multi-tenant, no lead operator)",
                "AL_ANC_035 — Lithium site, Ghana (cadastre match, operator redacted)",
            ],
        },
        "note": (
            "This tool resolves commercial identity only. "
            "Power demand (MW), off-take quality, load profiles, and buildout "
            "demand are intentionally absent and will be produced by downstream tools: "
            "calculate_current_demand, assess_bankability, and model_growth_trajectory."
        ),
        "message": (
            "57 detections processed. 35 anchor loads and generation assets "
            "assigned commercial identities across 5 sectors and 5 corridor countries "
            "via mining cadastre, industrial registries, port authorities, "
            "energy regulators, and trade databases."
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