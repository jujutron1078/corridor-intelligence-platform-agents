"""
Trade service — serves trade/commodity data.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from src.shared.pipeline.utils import DATA_DIR

logger = logging.getLogger("corridor.api.trade_service")

TRADE_DATA_DIR = DATA_DIR / "trade"

_prices_df: pd.DataFrame | None = None
_value_chain: dict | None = None
_trade_flows: dict[str, pd.DataFrame] = {}
_loaded = False


def init() -> None:
    """Load trade data into memory."""
    global _prices_df, _value_chain, _trade_flows, _loaded

    # Load commodity prices
    prices_path = TRADE_DATA_DIR / "commodity_prices.csv"
    if prices_path.exists():
        try:
            _prices_df = pd.read_csv(prices_path, parse_dates=["date"])
            logger.info("Loaded commodity prices: %d rows", len(_prices_df))
        except Exception as exc:
            logger.error("Failed to load prices: %s", exc)

    # Load value-chain analysis
    vc_path = TRADE_DATA_DIR / "value_chain_analysis.json"
    if vc_path.exists():
        try:
            with open(vc_path) as f:
                _value_chain = json.load(f)
            logger.info("Loaded value-chain analysis")
        except Exception as exc:
            logger.error("Failed to load value chain: %s", exc)

    # Load trade flow CSVs
    for f in TRADE_DATA_DIR.glob("trade_flows_*.csv"):
        commodity = f.stem.replace("trade_flows_", "")
        try:
            _trade_flows[commodity] = pd.read_csv(f)
            logger.info("Loaded trade flows for %s: %d rows", commodity, len(_trade_flows[commodity]))
        except Exception as exc:
            logger.error("Failed to load trade flows %s: %s", commodity, exc)

    _loaded = True


def is_loaded() -> bool:
    """Check if trade data is loaded."""
    return _loaded


def get_trade_flows(country: str, commodity: str) -> dict[str, Any]:
    """Get bilateral trade flow data for a country/commodity."""
    df = _trade_flows.get(commodity)
    if df is None:
        return {"error": f"No trade data for {commodity}", "data": []}

    mask = df["reporter_iso3"] == country
    filtered = df[mask]

    if filtered.empty:
        return {"error": f"No data for {country}/{commodity}", "data": []}

    # Summarize by year and flow type
    summary = (
        filtered.groupby(["year", "flow", "processing_stage"])
        .agg({"trade_value_usd": "sum", "net_weight_kg": "sum"})
        .reset_index()
    )

    return {
        "country": country,
        "commodity": commodity,
        "total_records": len(filtered),
        "data": summary.to_dict(orient="records"),
    }


# Common UN M49 → country name mapping for trade partners
_M49_NAMES: dict[int, str] = {
    0: "World", 4: "Afghanistan", 8: "Albania", 12: "Algeria", 20: "Andorra",
    24: "Angola", 28: "Antigua & Barbuda", 31: "Azerbaijan", 32: "Argentina",
    36: "Australia", 40: "Austria", 44: "Bahamas", 48: "Bahrain",
    50: "Bangladesh", 51: "Armenia", 52: "Barbados", 56: "Belgium",
    60: "Bermuda", 64: "Bhutan", 68: "Bolivia", 70: "Bosnia & Herzegovina",
    72: "Botswana", 76: "Brazil", 84: "Belize", 86: "British Indian Ocean Territory",
    92: "British Virgin Islands", 96: "Brunei", 100: "Bulgaria", 104: "Myanmar",
    108: "Burundi", 112: "Belarus", 116: "Cambodia", 120: "Cameroon",
    124: "Canada", 132: "Cape Verde", 136: "Cayman Islands",
    140: "Central African Republic", 144: "Sri Lanka", 148: "Chad",
    152: "Chile", 156: "China", 162: "Christmas Island", 166: "Cocos Islands",
    170: "Colombia", 174: "Comoros", 178: "Congo", 180: "DR Congo",
    184: "Cook Islands", 188: "Costa Rica", 191: "Croatia", 192: "Cuba",
    196: "Cyprus", 203: "Czechia", 204: "Benin", 208: "Denmark",
    212: "Dominica", 214: "Dominican Republic", 218: "Ecuador",
    222: "El Salvador", 226: "Equatorial Guinea", 231: "Ethiopia",
    233: "Estonia", 234: "Faroe Islands", 239: "Falkland Islands",
    246: "Finland", 251: "France", 258: "French Polynesia",
    260: "French Southern Territories", 262: "Djibouti", 266: "Gabon",
    268: "Georgia", 270: "Gambia", 275: "Palestine", 276: "Germany",
    288: "Ghana", 292: "Gibraltar", 296: "Kiribati", 300: "Greece",
    304: "Greenland", 308: "Grenada", 316: "Guam", 320: "Guatemala",
    324: "Guinea", 328: "Guyana", 332: "Haiti", 336: "Vatican",
    340: "Honduras", 344: "Hong Kong", 348: "Hungary", 352: "Iceland",
    356: "India", 360: "Indonesia", 364: "Iran", 368: "Iraq",
    372: "Ireland", 376: "Israel", 380: "Italy", 384: "Ivory Coast",
    388: "Jamaica", 392: "Japan", 398: "Kazakhstan", 400: "Jordan",
    404: "Kenya", 408: "North Korea", 410: "South Korea", 414: "Kuwait",
    417: "Kyrgyzstan", 422: "Lebanon", 426: "Lesotho", 428: "Latvia",
    430: "Liberia", 434: "Libya", 440: "Lithuania", 442: "Luxembourg",
    446: "Macao", 450: "Madagascar", 454: "Malawi", 458: "Malaysia",
    462: "Maldives", 466: "Mali", 470: "Malta", 478: "Mauritania",
    480: "Mauritius", 484: "Mexico", 490: "Taiwan", 496: "Mongolia",
    498: "Moldova", 499: "Montenegro", 500: "Montserrat", 504: "Morocco",
    508: "Mozambique", 512: "Oman", 516: "Namibia", 520: "Nauru",
    524: "Nepal", 528: "Netherlands", 531: "Curacao", 533: "Aruba",
    540: "New Caledonia", 548: "Vanuatu", 554: "New Zealand",
    558: "Nicaragua", 562: "Niger", 566: "Nigeria", 568: "Niue",
    574: "Norfolk Island", 577: "Northern Mariana Islands",
    579: "Norway", 584: "Marshall Islands", 585: "Palau",
    586: "Pakistan", 591: "Panama", 598: "Papua New Guinea",
    600: "Paraguay", 604: "Peru", 608: "Philippines", 612: "Pitcairn",
    616: "Poland", 620: "Portugal", 624: "Guinea-Bissau",
    634: "Qatar", 642: "Romania", 643: "Russia", 646: "Rwanda",
    654: "Saint Helena", 659: "Saint Kitts & Nevis", 660: "Anguilla",
    662: "Saint Lucia", 670: "Saint Vincent", 674: "San Marino",
    678: "Sao Tome & Principe", 682: "Saudi Arabia", 686: "Senegal",
    688: "Serbia", 690: "Seychelles", 694: "Sierra Leone", 699: "India",
    702: "Singapore", 703: "Slovakia", 704: "Vietnam", 705: "Slovenia",
    706: "Somalia", 710: "South Africa", 716: "Zimbabwe", 724: "Spain",
    729: "Sudan", 732: "Western Sahara", 740: "Suriname", 748: "Eswatini",
    752: "Sweden", 757: "Switzerland", 760: "Syria", 764: "Thailand",
    768: "Togo", 772: "Tokelau", 776: "Tonga", 780: "Trinidad & Tobago",
    784: "UAE", 788: "Tunisia", 792: "Turkey", 795: "Turkmenistan",
    796: "Turks & Caicos", 798: "Tuvalu", 800: "Uganda", 804: "Ukraine",
    807: "North Macedonia", 818: "Egypt", 826: "UK", 834: "Tanzania",
    838: "US Virgin Islands", 840: "USA", 842: "USA", 854: "Burkina Faso",
    858: "Uruguay", 860: "Uzbekistan", 862: "Venezuela", 887: "Yemen",
    894: "Zambia", 899: "Other",
}


# Country centroids for drawing trade arcs (lon, lat)
_COUNTRY_CENTROIDS: dict[str, tuple[float, float]] = {
    "NGA": (3.40, 6.45), "BEN": (2.42, 6.37), "TGO": (1.23, 6.17),
    "GHA": (-0.19, 5.60), "CIV": (-3.97, 5.36),
}
_M49_CENTROIDS: dict[int, tuple[float, float]] = {
    0: (0, 0), 4: (67.7, 33.9), 8: (20.2, 41.2), 12: (1.7, 28.0),
    20: (1.5, 42.5), 24: (17.9, -11.2), 28: (-61.8, 17.1), 31: (47.6, 40.1),
    32: (-63.6, -38.4), 36: (134, -25), 40: (14.6, 47.5), 44: (-77.4, 25.0),
    48: (50.6, 26.0), 50: (90.4, 23.7), 51: (45.0, 40.1), 52: (-59.5, 13.2),
    56: (4.4, 50.8), 60: (-64.8, 32.3), 64: (90.4, 27.5), 68: (-65.2, -16.3),
    70: (17.7, 43.9), 72: (24.7, -22.3), 76: (-51.9, -14.2), 84: (-88.5, 17.2),
    96: (114.7, 4.5), 100: (25.5, 42.7), 104: (96.0, 21.9),
    108: (29.9, -3.4), 112: (27.9, 53.7), 116: (105.0, 12.6),
    120: (12.4, 7.4), 124: (-106.3, 56.1), 132: (-24.0, 16.0),
    140: (20.9, 6.6), 144: (80.8, 7.9), 148: (18.7, 15.5),
    152: (-71.5, -35.7), 156: (104.2, 35.9), 170: (-74.3, 4.6),
    174: (43.9, -11.9), 178: (15.8, -0.2), 180: (21.8, -4.0),
    188: (-84.0, 9.7), 191: (15.2, 45.1), 192: (-77.8, 21.5),
    196: (33.4, 35.1), 203: (15.5, 49.8), 204: (2.42, 6.37),
    208: (9.5, 56.3), 212: (-61.4, 15.4), 214: (-70.2, 18.7),
    218: (-78.2, -1.8), 222: (-88.9, 13.8), 226: (10.3, 1.6),
    231: (40.5, 9.1), 233: (25.0, 58.6), 246: (25.7, 61.9),
    251: (2.2, 46.2), 258: (-149.4, -17.7), 262: (43.2, 11.6),
    266: (11.6, -0.8), 268: (43.4, 42.3), 270: (-15.3, 13.4),
    275: (35.2, 31.9), 276: (10.5, 51.2), 288: (-0.19, 5.60),
    296: (173.0, 1.9), 300: (21.8, 39.1), 304: (-42.6, 71.7),
    308: (-61.7, 12.1), 320: (-90.2, 15.8), 324: (-9.7, 9.9),
    328: (-58.9, 4.9), 332: (-72.3, 19.0), 340: (-86.2, 14.1),
    344: (114.1, 22.4), 348: (19.5, 47.2), 352: (-19.0, 65.0),
    356: (79, 21), 360: (113.9, -0.8), 364: (53.7, 32.4),
    368: (43.7, 33.2), 372: (-8.2, 53.4), 376: (34.8, 31.0),
    380: (12.6, 41.9), 384: (-3.97, 5.36), 388: (-77.3, 18.1),
    392: (138.3, 36.2), 398: (66.9, 48.0), 400: (36.2, 30.6),
    404: (37.9, -0.02), 408: (127.5, 40.3), 410: (127.8, 35.9),
    414: (47.5, 29.3), 417: (74.8, 41.2), 422: (35.9, 33.9),
    426: (28.2, -29.6), 428: (24.6, 56.9), 430: (-9.4, 6.4),
    434: (17.2, 26.3), 440: (23.9, 55.2), 442: (6.1, 49.8),
    446: (113.5, 22.2), 450: (46.9, -18.8), 454: (34.3, -13.3),
    458: (101.7, 3.1), 462: (73.2, 3.2), 466: (-8.0, 17.6),
    470: (14.4, 35.9), 478: (-10.9, 21.0), 480: (57.6, -20.3),
    484: (-102.6, 23.6), 490: (121.0, 23.7), 496: (103.8, 46.9),
    498: (28.4, 47.4), 499: (19.4, 42.7), 504: (-7.1, 31.8),
    508: (35.5, -18.7), 512: (55.9, 21.5), 516: (18.5, -22.6),
    524: (84.1, 28.4), 528: (5.3, 52.1), 540: (165.6, -22.3),
    548: (166.9, -15.4), 554: (174.9, -40.9), 558: (-85.2, 12.9),
    562: (8.1, 17.6), 566: (3.40, 6.45), 586: (69.3, 30.4),
    591: (-80.8, 8.5), 598: (143.9, -6.3), 600: (-58.4, -23.4),
    604: (-75.0, -9.2), 608: (121.8, 12.9), 616: (19.1, 51.9),
    620: (-8.2, 39.4), 624: (-15.2, 11.8), 634: (51.2, 25.4),
    642: (24.7, 45.9), 643: (105.3, 61.5), 646: (29.9, -1.9),
    662: (-61.0, 13.9), 670: (-61.3, 12.9), 678: (6.6, 0.2),
    682: (45.1, 23.9), 686: (-14.5, 14.5), 688: (21.0, 44.0),
    690: (55.5, -4.7), 694: (-11.8, 8.5), 702: (103.8, 1.4),
    703: (19.7, 48.7), 704: (108.3, 14.1), 705: (14.6, 46.2),
    706: (46.2, 5.2), 710: (22.9, -30.6), 716: (29.2, -19.0),
    724: (-3.7, 40.5), 729: (30.2, 12.9), 740: (-56.0, 3.9),
    748: (31.5, -26.5), 752: (18.6, 60.1), 757: (8.2, 46.8),
    760: (38.0, 34.8), 764: (100.5, 15.9), 768: (1.23, 6.17),
    776: (-175.2, -21.2), 780: (-61.2, 10.7), 784: (54.0, 23.4),
    788: (9.5, 33.9), 792: (35.2, 38.9), 800: (32.3, 1.4),
    804: (31.2, 48.4), 807: (21.7, 41.5), 818: (30.8, 26.8),
    826: (-3.4, 55.4), 834: (34.9, -6.4), 840: (-95.7, 37.1),
    842: (-95.7, 37.1), 854: (-1.6, 12.2), 858: (-55.8, -32.5),
    860: (64.6, 41.4), 862: (-66.6, 6.4), 887: (48.5, 15.6),
    894: (28.3, -15.4), 899: (0, 0),
}


def get_trade_arcs(country: str, commodity: str, top_n: int = 8) -> dict[str, Any]:
    """Return trade flow arcs with coordinates for map visualization."""
    df = _trade_flows.get(commodity)
    if df is None:
        return {"arcs": []}

    origin = _COUNTRY_CENTROIDS.get(country)
    if not origin:
        return {"arcs": []}

    mask = df["reporter_iso3"] == country
    filtered = df[mask]
    if filtered.empty:
        return {"arcs": []}

    # Determine which column has M49 numeric codes
    # Some datasets use numeric 'partner', others use 'partner_code'
    partner_is_numeric = pd.api.types.is_numeric_dtype(df.get("partner", pd.Series(dtype="object")))
    code_col = "partner" if partner_is_numeric else "partner_code"
    name_col = "partner" if not partner_is_numeric else None

    if code_col not in filtered.columns:
        return {"arcs": []}

    arcs = []
    for flow_dir in ["export", "import"]:
        flow_mask = filtered["flow"].str.lower() == flow_dir
        flow_df = filtered[flow_mask]
        if flow_df.empty:
            continue
        by_partner = (
            flow_df
            .groupby([code_col, "processing_stage"])
            .agg({"trade_value_usd": "sum"})
            .reset_index()
            .sort_values("trade_value_usd", ascending=False)
        )
        # Take top N unique partners
        seen: set[int] = set()
        for _, row in by_partner.iterrows():
            try:
                code = int(row[code_col])
            except (ValueError, TypeError):
                continue
            if code == 0 or code in seen:
                continue
            dest = _M49_CENTROIDS.get(code)
            if not dest:
                continue
            seen.add(code)
            if len(seen) > top_n:
                break
            # Resolve partner name
            partner_name = _M49_NAMES.get(code, "")
            if not partner_name and name_col:
                # Look up original name from the dataframe
                match = flow_df[flow_df[code_col] == code]
                if not match.empty and name_col in match.columns:
                    partner_name = str(match[name_col].iloc[0])
            if not partner_name:
                partner_name = f"Country {code}"

            arcs.append({
                "source": list(origin),
                "target": list(dest),
                "flow": flow_dir,
                "processing_stage": str(row.get("processing_stage", "unknown")),
                "trade_value_usd": float(row["trade_value_usd"]),
                "partner_name": partner_name,
                "commodity": commodity,
            })

    return {"country": country, "commodity": commodity, "arcs": arcs}


def get_top_partners(country: str, commodity: str, flow: str = "export", top_n: int = 10) -> dict[str, Any]:
    """Get top trade partners by value for a country/commodity/flow direction."""
    df = _trade_flows.get(commodity)
    if df is None:
        return {"error": f"No trade data for {commodity}", "partners": []}

    mask = (df["reporter_iso3"] == country)
    if "flow" in df.columns:
        mask = mask & (df["flow"].str.lower() == flow.lower())
    filtered = df[mask]

    if filtered.empty:
        return {"error": f"No partner data for {country}/{commodity}", "partners": []}

    # Determine which column to use for partner identification
    partner_is_numeric = pd.api.types.is_numeric_dtype(df.get("partner", pd.Series(dtype="object")))
    code_col = "partner" if partner_is_numeric else "partner_code"
    name_col = "partner" if not partner_is_numeric else None

    group_col = code_col if code_col in filtered.columns else "partner"

    # Group by partner, sum trade value
    agg_cols = {"trade_value_usd": "sum"}
    if "net_weight_kg" in filtered.columns:
        agg_cols["net_weight_kg"] = "sum"

    by_partner = (
        filtered.groupby(group_col)
        .agg(agg_cols)
        .reset_index()
        .sort_values("trade_value_usd", ascending=False)
        .head(top_n)
    )

    partners = []
    for _, row in by_partner.iterrows():
        try:
            code = int(row[group_col])
        except (ValueError, TypeError):
            code = 0
        # Resolve name
        p_name = _M49_NAMES.get(code, "")
        if not p_name and name_col and name_col in filtered.columns:
            match = filtered[filtered[group_col] == row[group_col]]
            if not match.empty:
                p_name = str(match[name_col].iloc[0])
        if not p_name:
            p_name = str(row[group_col]) if not partner_is_numeric else f"Country {code}"

        partners.append({
            "partner_code": code,
            "partner_name": p_name,
            "trade_value_usd": float(row["trade_value_usd"]),
            "net_weight_kg": float(row.get("net_weight_kg", 0)),
        })

    return {
        "country": country,
        "commodity": commodity,
        "flow": flow,
        "partners": partners,
    }


def get_value_chain(commodity: str) -> dict[str, Any]:
    """Get value-chain gap analysis for a commodity."""
    if _value_chain is None:
        # Compute on-the-fly if not pre-computed
        from src.pipelines.trade_pipeline.value_chain import compute_value_chain_gap
        return compute_value_chain_gap(commodity)

    result = _value_chain.get(commodity)
    if not result:
        return {"error": f"No value-chain data for {commodity}"}
    return result


def get_commodity_prices(
    commodity: str,
    start_year: int = 2015,
    end_year: int = 2024,
) -> dict[str, Any]:
    """Get monthly commodity price time-series."""
    if _prices_df is None or _prices_df.empty:
        # Try to parse on-the-fly
        from src.pipelines.trade_pipeline.pinksheet import get_commodity_prices as _get_prices
        df = _get_prices(commodity, start_year, end_year)
        if df.empty:
            return {"error": f"No price data for {commodity}", "data": []}
        return {
            "commodity": commodity,
            "data": df.to_dict(orient="records"),
        }

    mask = (
        (_prices_df["commodity"] == commodity)
        & (_prices_df["date"].dt.year >= start_year)
        & (_prices_df["date"].dt.year <= end_year)
    )
    filtered = _prices_df[mask].copy()

    if filtered.empty:
        return {"error": f"No price data for {commodity}", "data": []}

    filtered["date"] = filtered["date"].dt.strftime("%Y-%m-%d")
    return {
        "commodity": commodity,
        "data": filtered.to_dict(orient="records"),
    }
