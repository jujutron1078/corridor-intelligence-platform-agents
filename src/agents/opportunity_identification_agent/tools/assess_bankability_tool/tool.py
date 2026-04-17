import json
import logging

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import BankabilityInput

logger = logging.getLogger("corridor.agent.opportunity.bankability")

# Bankability scoring rules by facility type and operator characteristics
SECTOR_SCORES = {
    "port_facility": {"offtake": 0.85, "financial": 0.80, "contract": 0.75},
    "airport": {"offtake": 0.80, "financial": 0.75, "contract": 0.70},
    "industrial_zone": {"offtake": 0.70, "financial": 0.65, "contract": 0.60},
    "mineral_site": {"offtake": 0.75, "financial": 0.70, "contract": 0.65},
    "rail_network": {"offtake": 0.65, "financial": 0.60, "contract": 0.55},
    "border_crossing": {"offtake": 0.50, "financial": 0.45, "contract": 0.40},
}

# Confidence adjustment: higher detection confidence → higher bankability
CONFIDENCE_BONUS = 0.10


def _score_anchor(det: dict) -> dict:
    """Score a single anchor load for bankability."""
    det_type = det.get("type", "other")
    props = det.get("properties", {})
    confidence = det.get("confidence", 0.5)

    base = SECTOR_SCORES.get(det_type, {"offtake": 0.50, "financial": 0.45, "contract": 0.40})

    # Confidence-adjusted scores
    adj = min(confidence - 0.5, 1.0) * CONFIDENCE_BONUS
    offtake = min(base["offtake"] + adj, 1.0)
    financial = min(base["financial"] + adj, 1.0)
    contract = min(base["contract"] + adj, 1.0)

    composite = round(0.40 * offtake + 0.35 * financial + 0.25 * contract, 2)

    if composite >= 0.70:
        tier = "Tier 1"
        tier_label = "Bankable — can anchor project debt directly"
    elif composite >= 0.55:
        tier = "Tier 2"
        tier_label = "Viable with credit enhancement or government guarantee"
    else:
        tier = "Tier 3"
        tier_label = "High risk — requires blended finance or sovereign co-financing"

    offtake_label = "High" if offtake >= 0.75 else "Medium" if offtake >= 0.55 else "Low"
    financial_label = "Strong" if financial >= 0.75 else "Moderate" if financial >= 0.55 else "Weak"
    contract_label = "High" if contract >= 0.70 else "Medium" if contract >= 0.50 else "Low"

    return {
        "score": composite,
        "tier": tier,
        "tier_label": tier_label,
        "offtake_willingness": offtake_label,
        "financial_strength": financial_label,
        "contract_readiness": contract_label,
        "offtake_score": round(offtake, 2),
        "financial_score": round(financial, 2),
        "contract_score": round(contract, 2),
    }


@tool("assess_bankability", description=TOOL_DESCRIPTION)
def assess_bankability_tool(
    payload: BankabilityInput, runtime: ToolRuntime
) -> Command:
    """
    Evaluates commercial viability of each anchor load as a long-term
    transmission customer using real infrastructure detection data.
    """
    from src.adapters.pipeline_bridge import pipeline_bridge

    try:
        infra = pipeline_bridge.get_infrastructure_detections()
    except Exception as exc:
        logger.error("Infrastructure data unavailable: %s", exc)
        return Command(update={"messages": [ToolMessage(
            content=json.dumps({
                "error": str(exc),
                "bankability_scores": [],
                "message": "Cannot assess bankability — infrastructure data unavailable.",
            }),
            tool_call_id=runtime.tool_call_id,
        )]})

    detections = infra.get("detections", [])

    # Get sovereign risk data for country-level risk adjustment
    sovereign_risk_adjustment = {}
    try:
        sov_risk = pipeline_bridge.get_sovereign_risk()
        cpi_scores = sov_risk.get("cpi_scores", [])
        governance = sov_risk.get("governance", {})
        for entry in cpi_scores:
            country_code = entry.get("country_code", entry.get("country", ""))
            score = entry.get("score", entry.get("cpi_score", 50))
            if country_code:
                # CPI ranges 0-100; higher = less corrupt = lower risk
                # Convert to risk adjustment: CPI > 40 = positive, CPI < 30 = negative
                try:
                    cpi_val = float(score)
                    risk_adj = round((cpi_val - 35) / 100 * 0.10, 3)  # ±0.065 max
                    sovereign_risk_adjustment[country_code] = {
                        "cpi_score": cpi_val,
                        "risk_adjustment": risk_adj,
                        "governance": governance.get(country_code, {}),
                    }
                except (ValueError, TypeError):
                    pass
        logger.info("Sovereign risk data obtained for %d countries", len(sovereign_risk_adjustment))
    except Exception as exc:
        logger.warning("Sovereign risk data unavailable: %s", exc)

    # Enrich with live market intelligence via Tavily
    market_sentiment = 0.0  # -0.1 to +0.1 adjustment
    market_signals = []
    try:
        news = pipeline_bridge.search_corridor_news(
            query="West Africa infrastructure investment bankability power demand offtake agreement",
            max_results=3,
        )
        if news.get("status") == "success":
            positive = ["investment", "agreement", "funding", "approved", "expansion", "growth"]
            negative = ["default", "suspended", "delay", "cancel", "dispute", "bankrupt"]
            pos = neg = 0
            for item in news.get("results", []):
                content = item.get("content", "").lower()
                pos += sum(1 for kw in positive if kw in content)
                neg += sum(1 for kw in negative if kw in content)
                market_signals.append({"title": item.get("title", ""), "url": item.get("url", "")})
            if pos + neg > 0:
                market_sentiment = 0.05 * (pos - neg) / (pos + neg)
    except Exception as exc:
        logger.warning("Market intelligence unavailable: %s", exc)

    # Score each non-generation detection
    scores = []
    tier_counts = {"Tier 1": 0, "Tier 2": 0, "Tier 3": 0}
    total_score = 0.0
    generation_excluded = 0

    for i, det in enumerate(detections):
        det_type = det.get("type", "other")

        # Skip generation assets — they are supply, not demand
        if det_type == "power_plant":
            generation_excluded += 1
            continue

        props = det.get("properties", {})
        country = props.get("country", props.get("addr:country", "Unknown"))

        scoring = _score_anchor(det)
        # Apply market sentiment adjustment to financial score
        if market_sentiment != 0.0:
            scoring["score"] = round(min(1.0, max(0, scoring["score"] + market_sentiment)), 2)
        # Apply sovereign risk adjustment based on country CPI/governance
        if country in sovereign_risk_adjustment:
            sov_adj = sovereign_risk_adjustment[country]["risk_adjustment"]
            scoring["score"] = round(min(1.0, max(0, scoring["score"] + sov_adj)), 2)
            scoring["sovereign_risk_applied"] = True
            scoring["cpi_score"] = sovereign_risk_adjustment[country]["cpi_score"]
        entry = {
            "anchor_id": f"AL_ANC_{i + 1:03d}",
            "detection_id": det.get("detection_id", f"DET-{i + 1:03d}"),
            "entity_name": det.get("name", "Unknown"),
            "country": country,
            "type": det_type,
            **scoring,
        }
        scores.append(entry)
        tier_counts[scoring["tier"]] = tier_counts.get(scoring["tier"], 0) + 1
        total_score += scoring["score"]

    avg_score = round(total_score / len(scores), 2) if scores else 0.0

    response = {
        "corridor_average_score": avg_score,
        "anchor_loads_assessed": len(scores),
        "generation_assets_excluded": generation_excluded,
        "tier_summary": {
            "tier_1_count": tier_counts.get("Tier 1", 0),
            "tier_2_count": tier_counts.get("Tier 2", 0),
            "tier_3_count": tier_counts.get("Tier 3", 0),
        },
        "bankability_scores": scores,
        "sovereign_risk_adjustment": sovereign_risk_adjustment if sovereign_risk_adjustment else {},
        "market_intelligence": {
            "sentiment_adjustment": round(market_sentiment, 3),
            "signals": market_signals[:3],
        } if market_signals else {},
        "scoring_methodology": {
            "offtake_willingness_weight": 0.40,
            "financial_strength_weight": 0.35,
            "contract_readiness_weight": 0.25,
            "note": "Scores based on facility type, operator characteristics, detection confidence, live market signals, and sovereign risk (CPI/governance).",
        },
        "message": (
            f"Bankability assessed for {len(scores)} anchor loads. "
            f"Average score: {avg_score}. "
            f"Tier 1 (bankable): {tier_counts.get('Tier 1', 0)}, "
            f"Tier 2 (viable with enhancement): {tier_counts.get('Tier 2', 0)}, "
            f"Tier 3 (high risk): {tier_counts.get('Tier 3', 0)}."
        ),
    }

    return Command(update={"messages": [ToolMessage(
        content=json.dumps(response), tool_call_id=runtime.tool_call_id,
    )]})
