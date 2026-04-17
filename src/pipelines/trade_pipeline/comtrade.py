"""
UN Comtrade API client for bilateral trade flow data.

API: https://comtradeapi.un.org/
Requires free API key.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import pandas as pd
import requests

from src.shared.pipeline.aoi import COUNTRIES
from src.shared.pipeline.utils import RateLimiter, load_env, get_env, DATA_DIR, ensure_dir

logger = logging.getLogger("corridor.trade.comtrade")

COMTRADE_BASE_URL = "https://comtradeapi.un.org/data/v1/get/C/A/HS"
TRADE_DATA_DIR = DATA_DIR / "trade"

# Rate limit: free tier is very restrictive (~1 req/sec)
_rate_limiter = RateLimiter(max_calls=1, period_seconds=2)

# ── Corridor country codes (UN M49) ─────────────────────────────────────────

COUNTRY_M49 = {
    "NGA": 566,
    "BEN": 204,
    "TGO": 768,
    "GHA": 288,
    "CIV": 384,
}

# ── Key commodity HS codes ───────────────────────────────────────────────────

COMMODITY_HS_CODES = {
    "cocoa": {
        "raw": ["1801"],          # Cocoa beans
        "processed": ["1803", "1804", "1805", "1806"],  # Cocoa paste, butter, powder, chocolate
    },
    "gold": {
        "raw": ["7108"],          # Gold
        "processed": ["7113", "7114"],  # Jewelry, goldsmiths' articles
    },
    "bauxite": {
        "raw": ["2606"],          # Aluminium ores (bauxite)
        "processed": ["7601", "7604"],  # Unwrought aluminium, bars/rods
    },
    "oil": {
        "raw": ["2709"],          # Crude petroleum
        "processed": ["2710"],    # Petroleum oils (refined)
    },
    "rubber": {
        "raw": ["4001"],          # Natural rubber
        "processed": ["4011", "4012"],  # Rubber tires
    },
    "timber": {
        "raw": ["4403"],          # Wood in the rough
        "processed": ["4407", "4408", "4410"],  # Sawn wood, veneer, particle board
    },
}


def _get_api_key() -> str:
    """Get Comtrade API key from environment."""
    load_env()
    return get_env("COMTRADE_API_KEY", required=True)


def query_trade_flows(
    reporter_iso3: str,
    commodity_hs: str,
    year_start: int = 2015,
    year_end: int = 2023,
    flow_code: str = "X",  # X=export, M=import
) -> pd.DataFrame:
    """
    Query UN Comtrade for trade flow data.

    Args:
        reporter_iso3: Reporter country ISO3 code
        commodity_hs: HS commodity code (4 or 6 digit)
        year_start: Start year
        year_end: End year
        flow_code: 'X' for exports, 'M' for imports

    Returns:
        DataFrame with columns: year, reporter, partner, commodity_code,
        trade_value_usd, net_weight_kg, flow
    """
    api_key = _get_api_key()
    reporter_code = COUNTRY_M49.get(reporter_iso3)
    if not reporter_code:
        raise ValueError(f"Unknown country code: {reporter_iso3}")

    years = ",".join(str(y) for y in range(year_start, year_end + 1))

    params = {
        "reporterCode": str(reporter_code),
        "period": years,
        "cmdCode": commodity_hs,
        "flowCode": flow_code,
    }

    headers = {
        "Ocp-Apim-Subscription-Key": api_key,
    }

    _rate_limiter.wait()
    logger.info("Querying Comtrade: %s exports HS %s (%d-%d)", reporter_iso3, commodity_hs, year_start, year_end)

    try:
        resp = requests.get(COMTRADE_BASE_URL, params=params, headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        logger.error("Comtrade API error: %s", exc)
        return pd.DataFrame()

    records = data.get("data", [])
    if not records:
        logger.warning("No data returned for %s HS %s", reporter_iso3, commodity_hs)
        return pd.DataFrame()

    rows = []
    for r in records:
        rows.append({
            "year": r.get("period") or r.get("refYear"),
            "reporter": r.get("reporterDesc") or reporter_iso3,
            "reporter_iso3": reporter_iso3,
            "partner": r.get("partnerDesc") or str(r.get("partnerCode", "")),
            "partner_code": r.get("partnerCode"),
            "commodity_code": r.get("cmdCode"),
            "commodity_desc": r.get("cmdDesc") or commodity_hs,
            "trade_value_usd": r.get("primaryValue") or r.get("fobvalue") or 0,
            "net_weight_kg": r.get("netWgt") or 0,
            "flow": "export" if flow_code == "X" else "import",
        })

    df = pd.DataFrame(rows)
    logger.info("Got %d trade records for %s HS %s", len(df), reporter_iso3, commodity_hs)
    return df


def get_bilateral_flows(
    commodity: str,
    year_start: int = 2015,
    year_end: int = 2023,
) -> pd.DataFrame:
    """
    Get bilateral trade flows for a commodity across all 5 corridor countries.

    Pulls both raw and processed HS codes for the commodity.
    """
    hs_codes = COMMODITY_HS_CODES.get(commodity)
    if not hs_codes:
        raise ValueError(f"Unknown commodity: {commodity}. Available: {list(COMMODITY_HS_CODES.keys())}")

    all_data = []

    for country in COUNTRIES:
        for stage, codes in hs_codes.items():
            for hs_code in codes:
                # Exports
                df_x = query_trade_flows(country, hs_code, year_start, year_end, "X")
                if not df_x.empty:
                    df_x["commodity"] = commodity
                    df_x["processing_stage"] = stage
                    all_data.append(df_x)

                # Imports
                df_m = query_trade_flows(country, hs_code, year_start, year_end, "M")
                if not df_m.empty:
                    df_m["commodity"] = commodity
                    df_m["processing_stage"] = stage
                    all_data.append(df_m)

    if not all_data:
        return pd.DataFrame()

    combined = pd.concat(all_data, ignore_index=True)
    logger.info("Total bilateral flows for %s: %d records", commodity, len(combined))
    return combined


def save_trade_data(df: pd.DataFrame, name: str) -> None:
    """Save trade data to CSV."""
    ensure_dir(TRADE_DATA_DIR)
    path = TRADE_DATA_DIR / f"{name}.csv"
    df.to_csv(path, index=False)
    logger.info("Saved trade data: %s (%d rows)", path, len(df))
