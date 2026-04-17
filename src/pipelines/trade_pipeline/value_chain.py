"""
Value-chain gap analysis — raw vs. refined price differentials per commodity.
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from src.shared.pipeline.aoi import COUNTRIES, COUNTRY_NAMES
from .pinksheet import get_commodity_prices
from src.shared.pipeline.utils import DATA_DIR, ensure_dir

logger = logging.getLogger("corridor.trade.value_chain")

TRADE_DATA_DIR = DATA_DIR / "trade"

# ── Processing multipliers (approximate global averages) ─────────────────────
# For commodities where Pink Sheet doesn't have processed prices,
# we use industry-standard multipliers.

PROCESSING_MULTIPLIERS = {
    "cocoa": {
        "raw_product": "Cocoa beans",
        "processed_product": "Cocoa butter/powder",
        "multiplier": 3.2,  # Processed cocoa ~3.2x raw bean price
        "raw_price_per_ton": 3500,   # Approximate 2023 prices
        "processed_price_per_ton": 11200,
    },
    "gold": {
        "raw_product": "Gold ore/bullion",
        "processed_product": "Gold jewelry/articles",
        "multiplier": 5.0,
        "raw_price_per_ton": None,  # Gold priced per troy oz
        "processed_price_per_ton": None,
    },
    "bauxite": {
        "raw_product": "Bauxite ore",
        "processed_product": "Aluminium ingots",
        "multiplier": 8.5,  # Bauxite → Alumina → Aluminium
        "raw_price_per_ton": 50,
        "processed_price_per_ton": 2400,
    },
    "oil": {
        "raw_product": "Crude petroleum",
        "processed_product": "Refined petroleum products",
        "multiplier": 1.8,
        "raw_price_per_ton": 550,  # ~$75/bbl
        "processed_price_per_ton": 990,
    },
    "rubber": {
        "raw_product": "Natural rubber latex",
        "processed_product": "Rubber tires",
        "multiplier": 4.0,
        "raw_price_per_ton": 1500,
        "processed_price_per_ton": 6000,
    },
    "timber": {
        "raw_product": "Logs (round wood)",
        "processed_product": "Sawn wood / lumber",
        "multiplier": 2.5,
        "raw_price_per_ton": 200,
        "processed_price_per_ton": 500,
    },
}

# ── Country processing capabilities (approximate) ───────────────────────────
# Whether each country primarily exports raw or processed

COUNTRY_PROCESSING = {
    "cocoa": {
        "CIV": {"role": "major_producer", "processing_pct": 35, "notes": "World's largest cocoa producer, growing processing"},
        "GHA": {"role": "major_producer", "processing_pct": 25, "notes": "2nd largest producer, some processing"},
        "NGA": {"role": "producer", "processing_pct": 15, "notes": "Moderate production, limited processing"},
        "TGO": {"role": "transit", "processing_pct": 5, "notes": "Small production, mostly transit"},
        "BEN": {"role": "transit", "processing_pct": 2, "notes": "Minimal, mostly transit"},
    },
    "gold": {
        "GHA": {"role": "major_producer", "processing_pct": 10, "notes": "Africa's largest gold producer, mostly raw export"},
        "CIV": {"role": "producer", "processing_pct": 5, "notes": "Growing gold sector"},
        "NGA": {"role": "minor", "processing_pct": 2, "notes": "Small-scale mining"},
        "BEN": {"role": "transit", "processing_pct": 0, "notes": "Transit only"},
        "TGO": {"role": "minor", "processing_pct": 0, "notes": "Artisanal mining"},
    },
    "bauxite": {
        "GHA": {"role": "producer", "processing_pct": 20, "notes": "VALCO smelter (partial operations)"},
        "NGA": {"role": "minor", "processing_pct": 5, "notes": "Small deposits"},
        "CIV": {"role": "minor", "processing_pct": 0, "notes": "Minimal"},
        "TGO": {"role": "none", "processing_pct": 0, "notes": "N/A"},
        "BEN": {"role": "none", "processing_pct": 0, "notes": "N/A"},
    },
    "oil": {
        "NGA": {"role": "major_producer", "processing_pct": 15, "notes": "Major producer, refining deficit (imports refined products)"},
        "GHA": {"role": "producer", "processing_pct": 10, "notes": "Jubilee field, TEN, limited refining"},
        "CIV": {"role": "producer", "processing_pct": 30, "notes": "SIR refinery, better processing ratio"},
        "BEN": {"role": "minor", "processing_pct": 0, "notes": "Small offshore exploration"},
        "TGO": {"role": "none", "processing_pct": 0, "notes": "No significant production"},
    },
}


def compute_value_chain_gap(commodity: str) -> dict[str, Any]:
    """
    Compute the value-chain gap for a commodity across corridor countries.

    Returns:
        {
            "commodity": str,
            "raw_product": str,
            "processed_product": str,
            "raw_price": float,
            "processed_price": float,
            "multiplier": float,
            "gaps_by_country": {
                "NGA": {"processing_pct": 15, "missed_value_pct": 85, ...},
                ...
            }
        }
    """
    info = PROCESSING_MULTIPLIERS.get(commodity)
    if not info:
        raise ValueError(f"Unknown commodity: {commodity}. Available: {list(PROCESSING_MULTIPLIERS.keys())}")

    # Try to get live prices from Pink Sheet (graceful fallback if unavailable)
    try:
        prices_df = get_commodity_prices(commodity, start_year=2022, end_year=2024)
        if not prices_df.empty:
            latest_raw = prices_df[prices_df["stage"] == "raw"].sort_values("date").tail(1)
            if not latest_raw.empty:
                info = dict(info)  # copy
                info["raw_price_per_ton"] = float(latest_raw["price"].iloc[0])
    except Exception:
        logger.debug("Pink Sheet not available for %s, using fallback prices", commodity)

    country_gaps = {}
    country_data = COUNTRY_PROCESSING.get(commodity, {})

    for iso3 in COUNTRIES:
        country_info = country_data.get(iso3, {"role": "none", "processing_pct": 0, "notes": "N/A"})
        processing_pct = country_info["processing_pct"]
        missed_value_pct = 100 - processing_pct
        potential_value_usd = None

        if info.get("raw_price_per_ton") and info.get("processed_price_per_ton"):
            value_diff = info["processed_price_per_ton"] - info["raw_price_per_ton"]
            potential_value_usd = value_diff * (missed_value_pct / 100)

        country_gaps[iso3] = {
            "country_name": COUNTRY_NAMES.get(iso3, iso3),
            "role": country_info["role"],
            "processing_pct": processing_pct,
            "missed_value_pct": missed_value_pct,
            "potential_value_per_ton_usd": round(potential_value_usd, 2) if potential_value_usd else None,
            "notes": country_info["notes"],
        }

    return {
        "commodity": commodity,
        "raw_product": info["raw_product"],
        "processed_product": info["processed_product"],
        "raw_price": info.get("raw_price_per_ton"),
        "processed_price": info.get("processed_price_per_ton"),
        "multiplier": info["multiplier"],
        "gaps_by_country": country_gaps,
    }


def compute_all_value_chains() -> dict[str, dict]:
    """Compute value-chain gaps for all commodities."""
    results = {}
    for commodity in PROCESSING_MULTIPLIERS:
        try:
            results[commodity] = compute_value_chain_gap(commodity)
        except Exception as exc:
            logger.error("Failed to compute value chain for %s: %s", commodity, exc)
    return results


def save_value_chain_report(results: dict[str, dict]) -> None:
    """Save value-chain analysis to JSON."""
    import json
    ensure_dir(TRADE_DATA_DIR)
    path = TRADE_DATA_DIR / "value_chain_analysis.json"
    with open(path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    logger.info("Saved value-chain report: %s", path)
