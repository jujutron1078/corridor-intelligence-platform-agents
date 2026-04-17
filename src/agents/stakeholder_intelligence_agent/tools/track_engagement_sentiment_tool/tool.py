import json
import logging

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import SentimentTrackingInput

logger = logging.getLogger("corridor.agent.stakeholder.sentiment")

# Sentiment scoring baseline by stakeholder category
BASELINE_SENTIMENT = {
    "government": 0.70,       # generally supportive of infrastructure
    "dfi": 0.80,              # mandate-aligned
    "private_sector": 0.65,   # interested but cautious
    "community": 0.40,        # neutral, needs engagement
    "civil_society": 0.35,    # skeptical until safeguards confirmed
    "regional_body": 0.85,    # strongly supportive of integration
}


@tool("track_engagement_sentiment", description=TOOL_DESCRIPTION)
def track_engagement_sentiment_tool(
    payload: SentimentTrackingInput, runtime: ToolRuntime
) -> Command:
    """Monitors sentiment indicators and flags shifts in stakeholder support."""
    from src.adapters.pipeline_bridge import pipeline_bridge

    stakeholder_ids = payload.stakeholder_ids or []
    tracking_days = payload.tracking_period_days or 30

    # Get conflict data as proxy for community sentiment
    conflict_events = 0
    conflict_trend = "stable"
    try:
        conflict = pipeline_bridge.get_conflict_data()
        conflict_events = conflict.get("total_events", 0)
        # Rough trend: more events = declining community sentiment
        if conflict_events > 200:
            conflict_trend = "declining"
        elif conflict_events > 50:
            conflict_trend = "cautious"
        else:
            conflict_trend = "stable"
    except Exception as exc:
        logger.warning("Conflict data unavailable: %s", exc)

    # Get WB indicators for governance sentiment context
    governance_context = None
    try:
        wb = pipeline_bridge.get_worldbank_indicators()
        governance_context = wb.get("indicators")
    except Exception as exc:
        logger.warning("World Bank data unavailable: %s", exc)

    # Get sovereign risk data for governance-informed sentiment adjustment
    governance_sentiment_factor = {}
    governance_adjustment = 0.0
    try:
        sov_risk = pipeline_bridge.get_sovereign_risk()
        cpi_scores = sov_risk.get("cpi_scores", [])
        governance_data = sov_risk.get("governance", {})
        if cpi_scores:
            avg_cpi = sum(
                float(e.get("score", e.get("cpi_score", 35)))
                for e in cpi_scores if e.get("score") or e.get("cpi_score")
            ) / max(len(cpi_scores), 1)
            # Lower CPI = more corruption = negative sentiment for government/DFI engagement
            # CPI 30-50 typical for West Africa
            governance_adjustment = round((avg_cpi - 35) / 200, 3)  # ±0.075 range
            governance_sentiment_factor = {
                "average_cpi": round(avg_cpi, 1),
                "governance_indices": governance_data,
                "sentiment_adjustment": governance_adjustment,
                "source": sov_risk.get("source", "Transparency International / V-Dem"),
                "note": "Higher CPI scores indicate better governance, positively adjusting government/DFI sentiment",
            }
        logger.info("Sovereign risk data for sentiment: avg CPI %.1f, adjustment %.3f",
                     avg_cpi if cpi_scores else 0, governance_adjustment)
    except Exception as exc:
        logger.warning("Sovereign risk data unavailable for sentiment: %s", exc)

    # Get live news sentiment via Tavily
    news_results = []
    news_sentiment_adjustment = 0.0
    try:
        news = pipeline_bridge.search_corridor_news(
            query="Lagos Abidjan corridor infrastructure investment sentiment stakeholder",
            max_results=5,
        )
        if news.get("status") == "success":
            news_results = news.get("results", [])
            # Simple sentiment heuristic from news content
            positive_keywords = ["investment", "progress", "agreement", "partnership", "growth", "funding", "approved"]
            negative_keywords = ["delay", "protest", "opposition", "conflict", "dispute", "suspended", "cancel"]
            pos_count = neg_count = 0
            for item in news_results:
                content_lower = item.get("content", "").lower()
                pos_count += sum(1 for kw in positive_keywords if kw in content_lower)
                neg_count += sum(1 for kw in negative_keywords if kw in content_lower)
            if pos_count + neg_count > 0:
                news_sentiment_adjustment = 0.05 * (pos_count - neg_count) / (pos_count + neg_count)
    except Exception as exc:
        logger.warning("News search unavailable: %s", exc)

    # Get corridor countries
    try:
        corridor = pipeline_bridge.get_corridor_info()
        countries = corridor.get("countries", [])
    except Exception as exc:
        logger.warning("Corridor info unavailable: %s", exc)
        countries = ["NGA", "GHA", "CIV", "TGO", "BEN"]

    # Compute sentiment scores with conflict + news adjustment
    conflict_adjustment = 0.0
    if conflict_trend == "declining":
        conflict_adjustment = -0.15
    elif conflict_trend == "cautious":
        conflict_adjustment = -0.05

    sentiment_scores = {}
    for category, base_score in BASELINE_SENTIMENT.items():
        # Community and civil society most affected by conflict
        if category in ("community", "civil_society"):
            adjusted = base_score + conflict_adjustment + news_sentiment_adjustment
        elif category in ("government", "dfi"):
            # Government and DFI sentiment informed by governance quality
            adjusted = base_score + conflict_adjustment * 0.3 + news_sentiment_adjustment * 0.5 + governance_adjustment
        else:
            adjusted = base_score + conflict_adjustment * 0.3 + news_sentiment_adjustment * 0.5
        sentiment_scores[category] = round(max(0, min(1, adjusted)), 2)

    # Alerts based on sentiment thresholds
    alerts = []
    for category, score in sentiment_scores.items():
        if score < 0.40:
            alerts.append(f"LOW sentiment for {category} ({score}) — engagement intervention recommended")
        elif score < 0.50:
            alerts.append(f"Declining sentiment for {category} ({score}) — monitor closely")

    if conflict_trend == "declining":
        alerts.append(f"Conflict trend: {conflict_events} events detected — community engagement at risk")

    # Overall sentiment
    avg_sentiment = round(sum(sentiment_scores.values()) / len(sentiment_scores), 2)

    response = {
        "corridor_id": "AL_CORRIDOR_001",
        "analysis_type": "Engagement Sentiment Tracking",
        "tracking_period_days": tracking_days,
        "countries": countries,
        "sentiment_scores": sentiment_scores,
        "overall_sentiment": avg_sentiment,
        "sentiment_trend": conflict_trend,
        "conflict_context": {
            "total_events": conflict_events,
            "trend": conflict_trend,
            "community_impact": conflict_adjustment,
        },
        "alerts": alerts if alerts else ["No sentiment alerts — all categories within normal range"],
        "stakeholders_tracked": len(stakeholder_ids),
        "live_news": [
            {"title": r["title"], "url": r["url"]} for r in news_results[:3]
        ] if news_results else [],
        "governance_sentiment_factor": governance_sentiment_factor if governance_sentiment_factor else {},
        "news_sentiment_impact": round(news_sentiment_adjustment, 3),
        "data_sources": [
            "ACLED conflict data" if conflict_events > 0 else "ACLED (unavailable)",
            "Tavily live news" if news_results else "Tavily (unavailable)",
            "World Bank" if governance_context else "World Bank (unavailable)",
            "Sovereign Risk (CPI/V-Dem)" if governance_sentiment_factor else "Sovereign Risk (unavailable)",
            "Corridor AOI",
        ],
        "message": (
            f"Sentiment tracking: overall score {avg_sentiment} (trend: {conflict_trend}). "
            f"Government: {sentiment_scores.get('government', 'N/A')}, "
            f"Community: {sentiment_scores.get('community', 'N/A')}, "
            f"Private sector: {sentiment_scores.get('private_sector', 'N/A')}. "
            f"{len(alerts)} alert(s) raised. "
            f"Conflict events: {conflict_events}."
        ),
    }

    return Command(update={"messages": [ToolMessage(
        content=json.dumps(response), tool_call_id=runtime.tool_call_id,
    )]})
