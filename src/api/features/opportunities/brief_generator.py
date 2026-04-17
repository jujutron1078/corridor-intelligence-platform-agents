from datetime import datetime, timezone

from src.api.features.opportunities.schema import Opportunity


def _format_usd(value: float | None) -> str:
    if value is None:
        return "N/A"
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.1f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"${value / 1_000:.0f}K"
    return f"${value:,.0f}"


def generate_investment_brief(opportunities: list[Opportunity]) -> str:
    """Generate a Markdown investment brief from a list of opportunities."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Collect unique countries
    countries = sorted(set(o.country for o in opportunities))
    corridor_label = ", ".join(countries) if countries else "Lagos-Abidjan Corridor"

    lines = [
        f"# Investment Brief: {corridor_label}",
        f"**Date:** {now}",
        f"**Opportunities:** {len(opportunities)}",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
    ]

    # Summary stats
    total_value = sum(o.estimated_value_usd or 0 for o in opportunities)
    total_return = sum(o.estimated_return_usd or 0 for o in opportunities)
    total_jobs = sum(o.employment_impact or 0 for o in opportunities)
    avg_bankability = None
    bankability_scores = [o.bankability_score for o in opportunities if o.bankability_score is not None]
    if bankability_scores:
        avg_bankability = sum(bankability_scores) / len(bankability_scores)

    lines.append(
        f"This brief presents {len(opportunities)} investment "
        f"{'opportunity' if len(opportunities) == 1 else 'opportunities'} "
        f"identified along the Lagos-Abidjan economic corridor "
        f"spanning {corridor_label}."
    )
    lines.append("")

    summary_items = []
    if total_value > 0:
        summary_items.append(f"- **Total Estimated Investment:** {_format_usd(total_value)}")
    if total_return > 0:
        summary_items.append(f"- **Total Projected Economic Output:** {_format_usd(total_return)}")
    if total_jobs > 0:
        summary_items.append(f"- **Total Employment Impact:** {total_jobs:,} jobs")
    if avg_bankability is not None:
        summary_items.append(f"- **Average Bankability Score:** {avg_bankability:.2f}")

    if summary_items:
        lines.extend(summary_items)
        lines.append("")

    lines.extend(["---", "", "## Opportunities", ""])

    # Individual opportunities
    for i, opp in enumerate(opportunities, 1):
        lines.append(f"### {i}. {opp.title}")
        lines.append("")
        lines.append(f"- **Sector:** {opp.sector.title()}{f' ({opp.sub_sector})' if opp.sub_sector else ''}")
        lines.append(f"- **Country:** {opp.country}")
        if opp.location.get("name"):
            lines.append(f"- **Location:** {opp.location['name']}")
        lines.append(f"- **Status:** {opp.status.replace('_', ' ').title()}")

        if opp.bankability_score is not None:
            lines.append(f"- **Bankability Score:** {opp.bankability_score:.2f}")
        if opp.estimated_value_usd is not None:
            lines.append(f"- **Estimated Investment:** {_format_usd(opp.estimated_value_usd)}")
        if opp.estimated_return_usd is not None:
            lines.append(f"- **Projected Economic Output:** {_format_usd(opp.estimated_return_usd)}")
        if opp.employment_impact is not None:
            lines.append(f"- **Employment Impact:** {opp.employment_impact:,} jobs")
        if opp.gdp_multiplier is not None:
            lines.append(f"- **GDP Multiplier:** {opp.gdp_multiplier:.2f}x")
        if opp.risk_level:
            lines.append(f"- **Risk Level:** {opp.risk_level.title()}")

        lines.append("")

        if opp.summary:
            lines.append("**Summary:**")
            lines.append(opp.summary)
            lines.append("")

        if opp.analysis_detail:
            lines.append("**Analysis:**")
            lines.append(opp.analysis_detail)
            lines.append("")

        if opp.nearby_infrastructure:
            lines.append(f"**Nearby Infrastructure:** {', '.join(opp.nearby_infrastructure)}")
            lines.append("")

        # Justification sections
        if opp.methodology:
            lines.append("**Methodology:**")
            lines.append(opp.methodology)
            lines.append("")

        if opp.data_evidence:
            lines.append("**Data Evidence:**")
            lines.append("")
            lines.append("| Data Point | Value | Source | Year |")
            lines.append("|-----------|-------|--------|------|")
            for ev in opp.data_evidence:
                lines.append(f"| {ev.get('data_point', '')} | {ev.get('value', '')} | {ev.get('source', '')} | {ev.get('year', '')} |")
            lines.append("")

        if opp.calculations:
            lines.append("**Calculations:**")
            lines.append("")
            for calc_name, calc_data in opp.calculations.items():
                label = calc_name.replace("_", " ").title()
                lines.append(f"*{label}:*")
                if isinstance(calc_data, dict):
                    for k, v in calc_data.items():
                        k_label = k.replace("_", " ").title()
                        lines.append(f"- {k_label}: {v}")
                lines.append("")

        if opp.assumptions:
            lines.append("**Assumptions:**")
            for a in opp.assumptions:
                lines.append(f"- {a}")
            lines.append("")

        if opp.data_gaps:
            lines.append("**Data Gaps:**")
            for g in opp.data_gaps:
                lines.append(f"- {g}")
            lines.append("")

        if opp.risk_breakdown:
            lines.append("**Risk Breakdown:**")
            rb = opp.risk_breakdown
            for key in ["production_risk", "market_risk", "infrastructure_risk"]:
                level = rb.get(key, "")
                reasoning = rb.get(f"{key.replace('_risk', '')}_reasoning", rb.get(f"{key}_reasoning", ""))
                if level:
                    lines.append(f"- **{key.replace('_', ' ').title()}:** {level} — {reasoning}")
            lines.append("")

        if opp.data_sources:
            lines.append(f"**Data Sources:** {', '.join(opp.data_sources)}")
            lines.append("")

        lines.extend(["---", ""])

    # Methodology
    lines.extend([
        "## Methodology",
        "",
        "Analysis conducted using the Corridor Intelligence Platform's Value Detective "
        "methodology, cross-referencing 26+ data pipelines including FAO (agriculture), "
        "UNCTAD (trade), World Bank (indicators), OSM (infrastructure), satellite imagery "
        "(nightlights, NDVI), ACLED (conflict), and IMF (macroeconomic data).",
        "",
        "The Value Detective methodology applies four analytical pillars:",
        "",
        "1. **Trend Spotting** — Time-series analysis of economic activity indicators",
        "2. **Gap Analysis** — Infrastructure-production overlay to identify bottlenecks",
        "3. **Hidden Gems** — Multi-layer cross-referencing for non-obvious synergies",
        "4. **Actionable Wisdom** — Strategic implications with GDP multiplier and employment projections",
        "",
        "---",
        "",
        f"*Generated by the Corridor Intelligence Platform on {now}*",
        "",
    ])

    return "\n".join(lines)
