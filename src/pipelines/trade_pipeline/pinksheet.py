"""
World Bank Pink Sheet — monthly commodity price parser.

Downloads and parses the World Bank Commodity Price Data (Pink Sheet).
Source: https://www.worldbank.org/en/research/commodity-markets
"""

from __future__ import annotations

import logging
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from src.shared.pipeline.utils import DATA_DIR, ensure_dir

logger = logging.getLogger("corridor.trade.pinksheet")

TRADE_DATA_DIR = DATA_DIR / "trade"

# World Bank commodity price data URL (Excel format)
PINKSHEET_URL = "https://thedocs.worldbank.org/en/doc/5d903e848db1d1b83e0ec8f744e55570-0350012021/related/CMO-Historical-Data-Monthly.xlsx"

# Commodity column mappings (Pink Sheet column names → our commodity names)
# Column names match the actual "Monthly Prices" sheet headers
COMMODITY_COLUMNS = {
    "cocoa": {
        "raw": "Cocoa",
        "processed": None,
        "unit": "$/kg",
    },
    "gold": {
        "raw": "Gold",
        "processed": None,
        "unit": "$/troy oz",
    },
    "oil": {
        "raw": "Crude oil, Brent",
        "processed": None,
        "unit": "$/bbl",
    },
    "rubber": {
        "raw": "Rubber, TSR20 **",
        "processed": None,
        "unit": "cents/kg",
    },
    "timber": {
        "raw": "Logs, Cameroon",
        "processed": "Sawnwood, Cameroon",
        "unit": "$/cum",
    },
    "aluminum": {
        "raw": "Aluminum",
        "processed": None,
        "unit": "$/mt",
    },
}


def download_pinksheet(force: bool = False) -> Path:
    """Download the World Bank Pink Sheet Excel file."""
    ensure_dir(TRADE_DATA_DIR)
    path = TRADE_DATA_DIR / "pinksheet_monthly.xlsx"

    if path.exists() and not force:
        logger.info("Pink Sheet already downloaded: %s", path)
        return path

    logger.info("Downloading World Bank Pink Sheet...")
    resp = requests.get(PINKSHEET_URL, timeout=60)
    resp.raise_for_status()

    with open(path, "wb") as f:
        f.write(resp.content)

    logger.info("Downloaded Pink Sheet: %s (%d bytes)", path, len(resp.content))
    return path


def parse_pinksheet(path: Path | None = None) -> pd.DataFrame:
    """
    Parse the Pink Sheet Excel file into a tidy DataFrame.

    Returns: DataFrame with columns [date, commodity, price, unit].
    """
    if path is None:
        path = TRADE_DATA_DIR / "pinksheet_monthly.xlsx"

    if not path.exists():
        path = download_pinksheet()

    logger.info("Parsing Pink Sheet: %s", path)

    # The Pink Sheet has multiple sheets; monthly data is typically in 'Monthly Prices'
    try:
        df = pd.read_excel(path, sheet_name="Monthly Prices", header=None)
    except Exception:
        # Try first sheet
        df = pd.read_excel(path, sheet_name=0, header=None)

    # The Pink Sheet format: first column is date (YYYYMXX), subsequent columns are commodities
    # Find the header row (contains commodity names)
    header_row = None
    for i, row in df.iterrows():
        row_str = " ".join(str(v).upper() for v in row.values if pd.notna(v))
        if "CRUDE" in row_str or "COCOA" in row_str or "GOLD" in row_str:
            header_row = i
            break

    if header_row is None:
        logger.warning("Could not find header row in Pink Sheet, trying row 0")
        header_row = 0

    # Set headers and parse — skip the unit row right after the header
    headers = df.iloc[header_row].values
    df = df.iloc[header_row + 2:].copy()  # +2 to skip both header and unit row
    df.columns = [str(h).strip() if pd.notna(h) else f"col_{i}" for i, h in enumerate(headers)]

    # Find date column
    date_col = df.columns[0]

    # Convert to tidy format
    records = []
    for _, row in df.iterrows():
        date_val = row[date_col]
        if pd.isna(date_val):
            continue

        # Parse date (format varies: YYYYMM, YYYY-MM, etc.)
        try:
            date_str = str(date_val).strip()
            if "M" in date_str.upper():
                parts = date_str.upper().split("M")
                year = int(parts[0])
                month = int(parts[1])
            elif "-" in date_str:
                parts = date_str.split("-")
                year = int(parts[0])
                month = int(parts[1])
            else:
                continue

            date = pd.Timestamp(year=year, month=month, day=1)
        except (ValueError, IndexError):
            continue

        for commodity_name, col_info in COMMODITY_COLUMNS.items():
            raw_col = col_info["raw"]
            if raw_col and raw_col in df.columns:
                val = row.get(raw_col)
                if pd.notna(val):
                    try:
                        records.append({
                            "date": date,
                            "commodity": commodity_name,
                            "stage": "raw",
                            "price": float(val),
                            "unit": col_info["unit"],
                        })
                    except (ValueError, TypeError):
                        pass

            processed_col = col_info.get("processed")
            if processed_col and processed_col in df.columns:
                val = row.get(processed_col)
                if pd.notna(val):
                    try:
                        records.append({
                            "date": date,
                            "commodity": commodity_name,
                            "stage": "processed",
                            "price": float(val),
                            "unit": col_info["unit"],
                        })
                    except (ValueError, TypeError):
                        pass

    result = pd.DataFrame(records)
    if not result.empty:
        result = result.sort_values(["commodity", "date"]).reset_index(drop=True)

    logger.info("Parsed %d price records from Pink Sheet", len(result))
    return result


def get_commodity_prices(
    commodity: str,
    start_year: int = 2015,
    end_year: int = 2024,
) -> pd.DataFrame:
    """Get monthly prices for a specific commodity."""
    df = parse_pinksheet()
    if df.empty:
        return df

    mask = (
        (df["commodity"] == commodity)
        & (df["date"].dt.year >= start_year)
        & (df["date"].dt.year <= end_year)
    )
    return df[mask].copy()


def save_prices(df: pd.DataFrame, name: str = "commodity_prices") -> None:
    """Save parsed prices to CSV."""
    ensure_dir(TRADE_DATA_DIR)
    path = TRADE_DATA_DIR / f"{name}.csv"
    df.to_csv(path, index=False)
    logger.info("Saved prices: %s (%d rows)", path, len(df))
