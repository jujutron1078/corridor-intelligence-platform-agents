import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import DFIMatchingInput


@tool("match_dfi_institutions", description=TOOL_DESCRIPTION)
def match_dfi_institutions_tool(
    payload: DFIMatchingInput, runtime: ToolRuntime
) -> Command:
    """Matches the project to potential DFI funders based on mandate and eligibility."""

    # In a real-world scenario, this tool would:
    # 1. Query a live database of DFI investment mandates, filtered by country IDA/IBRD status.
    # 2. Score institutions using a weighted mandate-match algorithm across sector, geography,
    #    ticket size, development theme, and historical West Africa appetite.
    # 3. Pull real-time pipeline data to check each DFI's current capital availability.
    # 4. Apply exclusion filters (e.g., World Bank debarment lists, ESG screens).
    # 5. Return a sequenced engagement plan based on concessionality anchor logic:
    #    the institution with the highest concessional firepower is approached first
    #    to set the blended finance anchor that unlocks commercial tranches.

    # --- Mock: Derived from payload for realism ---
    countries = payload.corridor_countries        # e.g. ["Côte d'Ivoire", "Ghana", "Togo", "Benin", "Nigeria"]
    sectors = payload.sectors                     # e.g. ["Transmission", "Solar", "Digital", "Agro-Processing"]
    impact = payload.development_impact_metrics   # e.g. {"jobs_created": 95000, "gdp_uplift_usd": 4700000000}

    response = {

        # ------------------------------------------------------------------ #
        #  ELIGIBLE INSTITUTIONS                                               #
        #  Production: scored dynamically against live mandate database.       #
        #  Mock: pre-scored against Abidjan-Lagos corridor characteristics.    #
        # ------------------------------------------------------------------ #
        "eligible_institutions": [
            {
                "name": "African Development Bank (AfDB)",
                "abbreviation": "AfDB",
                "focus": "Regional Integration & Energy Access",
                "relevance": 0.98,
                "mandate_match_reasons": [
                    "Pan-African mandate covers all 5 corridor countries",
                    "WAPP (West African Power Pool) coordination role",
                    "SAPZ program directly funds agro-processing zones",
                    "High-priority regional integration ticket"
                ],
                "instrument_types": ["Concessional Loan", "Grant", "Equity", "Guarantee"],
                "typical_ticket_size_usd": "50M–500M",
                "concessional_rate_range": "2%–4%",
                "tenor_range_years": "20–30",
                "grace_period_years": 5,
                "country_eligibility": {
                    "Côte d'Ivoire": "ADB (non-concessional)",
                    "Ghana": "ADB (non-concessional)",
                    "Togo": "ADF (concessional)",
                    "Benin": "ADF (concessional)",
                    "Nigeria": "ADB (non-concessional)"
                },
                "current_pipeline_capacity_usd": "300M available for West Africa energy FY2026",
                "key_contact_division": "Power Systems & Energy Division (PSEN)",
                "esg_requirements": ["ESAP compliance", "Climate co-benefit minimum 40%"],
                "historical_west_africa_deals": 23,
                "avg_approval_timeline_months": 14
            },
            {
                "name": "EU Global Gateway",
                "abbreviation": "EU-GG",
                "focus": "Green Energy, Digital Infrastructure & Climate",
                "relevance": 0.93,
                "mandate_match_reasons": [
                    "West Africa Priority Region under Team Europe Initiative",
                    "Cross-border transmission aligns with Green Gateway pillar",
                    "Fiber optic co-deployment matches Digital Connectivity goals",
                    "Blended finance facility (EFSD+) available for private sector leverage"
                ],
                "instrument_types": ["Grant", "Blended Finance Guarantee", "Technical Assistance"],
                "typical_ticket_size_usd": "50M–200M (grant component)",
                "concessional_rate_range": "Grant (0%)",
                "tenor_range_years": "N/A (grant)",
                "grace_period_years": "N/A",
                "country_eligibility": {
                    "Côte d'Ivoire": "Eligible",
                    "Ghana": "Eligible",
                    "Togo": "Eligible",
                    "Benin": "Eligible",
                    "Nigeria": "Eligible"
                },
                "current_pipeline_capacity_usd": "€150M earmarked for West Africa clean energy 2025–2027",
                "key_contact_division": "DG INTPA – West Africa Regional Team",
                "esg_requirements": ["Paris Agreement alignment", "DNSH (Do No Significant Harm) assessment"],
                "historical_west_africa_deals": 11,
                "avg_approval_timeline_months": 18
            },
            {
                "name": "International Finance Corporation (IFC)",
                "abbreviation": "IFC",
                "focus": "Private Sector Infrastructure & Capital Markets",
                "relevance": 0.88,
                "mandate_match_reasons": [
                    "Largest global development finance institution for private sector",
                    "Lekki FTZ and Dangote anchor loads are IFC-eligible private sector clients",
                    "IFC InfraVentures can fund early-stage preparation costs",
                    "MIGA (sister entity) provides political risk insurance for commercial lenders"
                ],
                "instrument_types": ["Senior Loan", "Equity", "Quasi-Equity", "Guarantee (via MIGA)"],
                "typical_ticket_size_usd": "50M–300M",
                "concessional_rate_range": "SOFR + 2.5%–3.5% (market rate)",
                "tenor_range_years": "12–18",
                "grace_period_years": 3,
                "country_eligibility": {
                    "Côte d'Ivoire": "IDA PSW eligible",
                    "Ghana": "IBRD eligible",
                    "Togo": "IDA PSW eligible",
                    "Benin": "IDA PSW eligible",
                    "Nigeria": "IBRD eligible"
                },
                "current_pipeline_capacity_usd": "IFC has $2.1B allocated for Sub-Saharan Africa infrastructure FY2026",
                "key_contact_division": "Infrastructure & Natural Resources – Sub-Saharan Africa",
                "esg_requirements": ["IFC Performance Standards PS1–PS8", "GRID methodology for GHG accounting"],
                "historical_west_africa_deals": 34,
                "avg_approval_timeline_months": 12
            },
            {
                "name": "World Bank (IDA/IBRD)",
                "abbreviation": "WB",
                "focus": "Public Sector Infrastructure & Policy Reform",
                "relevance": 0.85,
                "mandate_match_reasons": [
                    "IDA credits available for Togo, Benin, Côte d'Ivoire (concessional)",
                    "WAPP Interconnection program already active in region",
                    "Guarantees program (IBRD PRG) can de-risk commercial debt tranche",
                    "Strong policy reform leverage (sector regulation, tariff reform)"
                ],
                "instrument_types": ["IDA Credit", "IBRD Loan", "Partial Risk Guarantee (PRG)", "Project Preparation Facility"],
                "typical_ticket_size_usd": "100M–500M",
                "concessional_rate_range": "1.25%–2% (IDA) / SOFR + 0.5% (IBRD)",
                "tenor_range_years": "25–40 (IDA) / 15–25 (IBRD)",
                "grace_period_years": "5 (IDA) / 3 (IBRD)",
                "country_eligibility": {
                    "Côte d'Ivoire": "IDA blend",
                    "Ghana": "IBRD",
                    "Togo": "IDA",
                    "Benin": "IDA",
                    "Nigeria": "IBRD"
                },
                "current_pipeline_capacity_usd": "$800M available under WAPP Phase 3 program",
                "key_contact_division": "Energy & Extractives GP – Africa Region",
                "esg_requirements": ["ESF (Environmental & Social Framework)", "ESCP required"],
                "historical_west_africa_deals": 41,
                "avg_approval_timeline_months": 20
            },
            {
                "name": "U.S. International Development Finance Corporation (DFC)",
                "abbreviation": "DFC",
                "focus": "U.S. Strategic Private Sector Investment",
                "relevance": 0.76,
                "mandate_match_reasons": [
                    "Prosper Africa initiative targets West African energy sector",
                    "Dangote Refinery and Lekki FTZ align with DFC private sector mandate",
                    "Political Risk Insurance available for U.S.-linked investors",
                    "Potential interest in fiber optic and data center components"
                ],
                "instrument_types": ["Direct Loan", "Loan Guarantee", "Political Risk Insurance", "Equity"],
                "typical_ticket_size_usd": "50M–250M",
                "concessional_rate_range": "SOFR + 2%–3% (near-market)",
                "tenor_range_years": "10–20",
                "grace_period_years": 2,
                "country_eligibility": {
                    "Côte d'Ivoire": "Eligible",
                    "Ghana": "Eligible",
                    "Togo": "Eligible",
                    "Benin": "Eligible",
                    "Nigeria": "Eligible"
                },
                "current_pipeline_capacity_usd": "$500M available under Prosper Africa energy allocation",
                "key_contact_division": "Office of Development Credit – Africa",
                "esg_requirements": ["OPIC Environmental Handbook standards", "U.S. nexus preferred"],
                "historical_west_africa_deals": 9,
                "avg_approval_timeline_months": 10
            },
            {
                "name": "Agence Française de Développement (AFD)",
                "abbreviation": "AFD",
                "focus": "Francophone Africa Development & Climate",
                "relevance": 0.81,
                "mandate_match_reasons": [
                    "Strong bilateral relationships with Côte d'Ivoire, Togo, and Benin",
                    "SUNREF program funds renewable energy in West Africa",
                    "Proparco (private sector arm) active in regional energy",
                    "Climate finance expertise aligns with solar + storage component"
                ],
                "instrument_types": ["Concessional Loan", "Grant", "Equity (via Proparco)", "Technical Assistance"],
                "typical_ticket_size_usd": "30M–150M",
                "concessional_rate_range": "1.5%–3.5%",
                "tenor_range_years": "20–25",
                "grace_period_years": 5,
                "country_eligibility": {
                    "Côte d'Ivoire": "Priority country",
                    "Ghana": "Eligible",
                    "Togo": "Priority country",
                    "Benin": "Priority country",
                    "Nigeria": "Eligible"
                },
                "current_pipeline_capacity_usd": "€200M allocated for West Africa climate/energy 2025–2027",
                "key_contact_division": "AFD West Africa Regional Hub – Abidjan",
                "esg_requirements": ["AFD Exclusion List compliance", "Climate co-benefit tracking"],
                "historical_west_africa_deals": 28,
                "avg_approval_timeline_months": 16
            }
        ],

        # ------------------------------------------------------------------ #
        #  ENGAGEMENT SEQUENCE                                                 #
        #  Production: optimized by concessionality-anchor logic + timeline.  #
        #  Mock: pre-built for Abidjan-Lagos blended structure.               #
        # ------------------------------------------------------------------ #
        "engagement_sequence": [
            {
                "step": 1,
                "institution": "AfDB",
                "rationale": "Approach first to secure concessional anchor loan ($250M). AfDB's WAPP coordination role gives them political leverage to unlock country approvals across all 5 nations. Their commitment signals credibility to all subsequent funders.",
                "target_instrument": "Concessional Loan – $250M @ 3%, 25-year",
                "timing": "Month 1–3 (parallel with project preparation)",
                "key_ask": "ADF/ADB blended loan + SAPZ co-financing for agro-processing zones"
            },
            {
                "step": 2,
                "institution": "EU Global Gateway / AFD",
                "rationale": "Approach jointly. EU grant reduces overall WACC and improves equity returns. AFD's Francophone relationships accelerate approvals in Côte d'Ivoire, Togo, and Benin. Combined ask of ~$120M in grants and concessional debt.",
                "target_instrument": "EU Grant – $80M + AFD Concessional Loan – $60M",
                "timing": "Month 2–5",
                "key_ask": "Climate finance grant for renewable integration + Francophone country facilitation"
            },
            {
                "step": 3,
                "institution": "World Bank (IDA/IBRD)",
                "rationale": "Engage for IDA credits in Togo and Benin (highest concessional need) and IBRD for Ghana and Nigeria. PRG instrument critical for de-risking commercial debt tranche. Policy reform conditionality helps fix tariff and regulatory gaps.",
                "target_instrument": "IDA Credit – $100M + IBRD PRG – $150M coverage",
                "timing": "Month 3–7",
                "key_ask": "Partial Risk Guarantee to unlock commercial bank participation"
            },
            {
                "step": 4,
                "institution": "IFC",
                "rationale": "Once concessional anchor is set by AfDB/WB/EU, engage IFC to lead the commercial senior debt tranche. IFC's market signal attracts other commercial lenders. MIGA political risk insurance covers the remaining bankability gap for private equity.",
                "target_instrument": "Senior Loan – $200M + MIGA PRI coverage",
                "timing": "Month 5–9",
                "key_ask": "A/B loan structure to mobilize additional commercial banks alongside IFC"
            },
            {
                "step": 5,
                "institution": "DFC",
                "rationale": "Approach last for top-up financing on the digital infrastructure and data center components. DFC's Prosper Africa mandate aligns with Lagos/Lekki digital hub. Useful for political risk coverage for U.S.-linked equity investors.",
                "target_instrument": "Direct Loan – $80M (digital component)",
                "timing": "Month 7–11",
                "key_ask": "PRI for U.S. equity investors + digital infrastructure loan"
            }
        ],

        # ------------------------------------------------------------------ #
        #  SUMMARY METADATA                                                    #
        # ------------------------------------------------------------------ #
        "summary": {
            "total_institutions_scanned": 24,
            "eligible_count": 6,
            "total_concessional_capacity_usd": "810M",
            "total_commercial_capacity_usd": "480M",
            "estimated_blended_wacc_range": "5.2%–6.8%",
            "highest_relevance_institution": "AfDB",
            "fastest_approval_institution": "DFC (avg 10 months)",
            "engagement_timeline_months": 11,
            "countries_with_full_coverage": ["Côte d'Ivoire", "Ghana", "Togo", "Benin", "Nigeria"]
        },

        "message": (
            "DFI matching complete across 24 institutions. 6 eligible funders identified with strong "
            "mandate alignment for the Abidjan-Lagos corridor. AfDB leads as concessional anchor "
            "(relevance: 0.98) given WAPP coordination role and pan-African mandate. "
            "Combined concessional capacity of $810M available across AfDB, EU, AFD, and World Bank. "
            "IFC recommended to lead the commercial senior debt tranche after concessional anchor is "
            "confirmed. Estimated blended WACC of 5.2%–6.8% achievable with recommended structure. "
            "Proceed to `generate_financing_scenarios` with these institutions as inputs."
        )
    }

    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=json.dumps(response),
                    tool_call_id=runtime.tool_call_id
                )
            ]
        }
    )