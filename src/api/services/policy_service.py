"""
Policy service — serves investment, environmental, and trade policy data
for the 5 corridor countries + ECOWAS/AfCFTA regional frameworks.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from src.shared.pipeline.utils import DATA_DIR

logger = logging.getLogger("corridor.api.policy_service")

POLICY_DIR = DATA_DIR / "policy"
VDEM_DIR = DATA_DIR / "vdem"

_corridor_policy: dict[str, Any] = {}
_governance: list[dict[str, Any]] = []
_loaded = False


def init() -> None:
    """Load policy and governance data."""
    global _corridor_policy, _governance, _loaded

    # Load consolidated corridor policy
    path = POLICY_DIR / "corridor_policy.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            _corridor_policy = json.load(f)
        logger.info("Policy service loaded: %d country records + regional", len(_corridor_policy) - 1)
    else:
        logger.warning("No corridor_policy.json found at %s", path)

    # Load V-Dem governance indicators
    gov_path = VDEM_DIR / "governance.json"
    if gov_path.exists():
        with open(gov_path, encoding="utf-8") as f:
            _governance = json.load(f)
        logger.info("Governance indicators loaded: %d records", len(_governance))

    _loaded = True


def is_loaded() -> bool:
    return _loaded


def get_policies(
    country: str | None = None,
    category: str | None = None,
) -> dict[str, Any]:
    """
    Get policy data, optionally filtered by country ISO3 and/or category.
    Categories: investment, environment, trade.
    """
    if country:
        data = _corridor_policy.get(country.upper(), {})
        if category:
            return {category: data.get(category, {})}
        return data

    if category:
        result = {}
        for code, policies in _corridor_policy.items():
            if code == "REGIONAL":
                continue
            if isinstance(policies, dict) and category in policies:
                result[code] = {category: policies[category]}
        return result

    return _corridor_policy


def get_comparison() -> dict[str, Any]:
    """Cross-country policy comparison for key metrics."""
    countries = ["CIV", "GHA", "NGA", "BEN", "TGO"]
    comparison = []

    for code in countries:
        data = _corridor_policy.get(code, {})
        inv = data.get("investment", {})
        env = data.get("environment", {})
        trade_agreements = data.get("trade", {}).get("agreements", [])
        meta = data.get("_metadata", {})
        incentives = inv.get("incentives", {})

        comparison.append({
            "country": code,
            "country_name": meta.get("country_name", code),
            "investment": {
                "tax_holiday_years": incentives.get("tax_holiday", {}).get("years"),
                "customs_exemption": incentives.get("customs_duty_exemption", False),
                "vat_exemption": incentives.get("vat_exemption", False),
                "epz_corporate_tax": incentives.get("epz_benefits", {}).get("corporate_tax"),
                "local_employment_pct": inv.get("local_employment_requirement"),
                "one_stop_shop": inv.get("one_stop_shop", False),
                "sector_priorities": inv.get("sector_priorities", []),
                "minimum_investment": inv.get("minimum_investment", {}),
                "approval_days": inv.get("approval_timelines", {}),
                "bilateral_treaties": inv.get("bilateral_investment_treaties", 0),
            },
            "environment": {
                "eia_timeline_days": env.get("eia", {}).get("timeline_days"),
                "eia_cost_range": env.get("eia", {}).get("cost_range"),
                "afforestation_ratio": env.get("compensation", {}).get("afforestation_ratio"),
            },
            "trade_agreements": [a.get("name") for a in trade_agreements],
        })

    return {
        "countries": comparison,
        "regional": _corridor_policy.get("REGIONAL", {}),
    }


def get_governance() -> dict[str, Any]:
    """Get V-Dem governance indicators for all corridor countries."""
    return {"data": _governance}


def get_policy_context_for_agents() -> str:
    """
    Build a compact policy summary string for injection into agent prompts.
    This ensures agents consider regulatory frameworks in their decisions.
    """
    lines = ["## Corridor Policy Framework (must inform all recommendations)\n"]

    for code in ["CIV", "GHA", "NGA", "BEN", "TGO"]:
        data = _corridor_policy.get(code, {})
        inv = data.get("investment", {})
        env = data.get("environment", {})
        incentives = inv.get("incentives", {})
        meta = data.get("_metadata", {})
        name = meta.get("country_name", code)

        tax = incentives.get("tax_holiday", {})
        lines.append(f"**{name} ({code})**: Tax holiday {tax.get('years', '?')}yr "
                      f"({'customs+VAT exempt' if incentives.get('customs_duty_exemption') else 'limited exemptions'}), "
                      f"EIA {env.get('eia', {}).get('timeline_days', '?')}d, "
                      f"local employment ≥{inv.get('local_employment_requirement', '?')}%, "
                      f"min investment {_fmt_currency(inv.get('minimum_investment', {}).get('general'))}, "
                      f"sectors: {', '.join(inv.get('sector_priorities', [])[:4])}")

    # Regional
    regional = _corridor_policy.get("REGIONAL", {})
    if regional:
        lines.append("\n**Regional**: AfCFTA (tariff liberalization 90%+), "
                      "ECOWAS CET (4 bands: 0/5/10/35%), "
                      "ECOWAS Investment Code (equal treatment, free transfer of capital)")

    lines.append("\n**Rule**: Always cite relevant policy when recommending investments, "
                  "routes, or infrastructure. Flag regulatory risks. "
                  "Consider EIA timelines and local content requirements in cost/time estimates.")

    return "\n".join(lines)


def _fmt_currency(value: Any) -> str:
    if value is None:
        return "?"
    v = float(value)
    if v >= 1e9:
        return f"₣{v / 1e9:.0f}B FCFA"
    if v >= 1e6:
        return f"₣{v / 1e6:.0f}M FCFA"
    return f"₣{v:,.0f}"
