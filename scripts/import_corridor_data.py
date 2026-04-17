#!/usr/bin/env python3
"""
Import and normalize corridor datasets from Downloads/Corridors into monorepo data/.

Handles:
- Windows-1252 encoding fix for Projects JSON
- Country code normalization to ISO3
- CSV → JSON conversion
- Roads summary pre-computation
- Output to corridor-monorepo/data/ directories
"""

import csv
import json
import io
from pathlib import Path
from collections import Counter, defaultdict

DOWNLOADS = Path("/Users/mohammedgudle/Downloads/Corridors")
DATA_DIR = Path(__file__).parent.parent / "data"

COUNTRY_MAP = {
    "benin": "BEN",
    "bénin": "BEN",
    "côte d'ivoire": "CIV",
    "cote d'ivoire": "CIV",
    "ivory coast": "CIV",
    "ghana": "GHA",
    "nigeria": "NGA",
    "togo": "TGO",
}


def normalize_country(value):
    """Normalize country name or code to ISO3."""
    if not value:
        return value
    v = str(value).strip()
    # Already ISO3
    if v.upper() in ("BEN", "CIV", "GHA", "NGA", "TGO"):
        return v.upper()
    # Full name lookup
    mapped = COUNTRY_MAP.get(v.lower())
    if mapped:
        return mapped
    return v


def normalize_record(record):
    """Normalize country fields in a record dict."""
    for key in ("country", "country_code", "country_name", "region"):
        if key in record and record[key]:
            record[key] = normalize_country(record[key])
    # Handle 'countries' field (comma-separated or list)
    if "countries" in record:
        val = record["countries"]
        if isinstance(val, list):
            record["countries"] = [normalize_country(c) for c in val]
        elif isinstance(val, str) and "," in val:
            record["countries"] = [normalize_country(c.strip()) for c in val.split(",")]
    return record


def load_json_safe(path):
    """Load JSON with fallback encoding handling."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (UnicodeDecodeError, json.JSONDecodeError):
        # Try Windows-1252
        with open(path, "r", encoding="windows-1252") as f:
            text = f.read()
        # Replace smart quotes and dashes
        text = text.replace("\u2019", "'").replace("\u2018", "'")
        text = text.replace("\u201c", '"').replace("\u201d", '"')
        text = text.replace("\u2013", "-").replace("\u2014", "-")
        return json.loads(text)


def load_csv_as_list(path):
    """Load CSV and return list of dicts."""
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def write_json(data, path):
    """Write JSON with UTF-8 encoding."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  -> {path} ({len(data) if isinstance(data, list) else 'dict'})")


def import_manufacturing():
    """Import manufacturing/industry company data."""
    print("\n=== Manufacturing ===")
    src = DOWNLOADS / "manufacturing-industry" / "output"
    json_files = sorted(src.glob("ALL_companies_*.json"))
    if not json_files:
        print("  SKIP: no ALL_companies JSON found")
        return
    data = load_json_safe(json_files[0])
    if isinstance(data, dict) and "companies" in data:
        records = data["companies"]
    elif isinstance(data, list):
        records = data
    else:
        records = [data]
    records = [normalize_record(r) for r in records]
    write_json(records, DATA_DIR / "manufacturing" / "companies.json")


def import_policy():
    """Import policy/regulatory data."""
    print("\n=== Policy ===")
    src = DOWNLOADS / "policy_dataV2" / "policy_dataV2"
    # Corridor-wide comparison
    corridor_files = sorted(src.glob("corridor_policy_data_*.json"))
    if corridor_files:
        data = load_json_safe(corridor_files[0])
        if isinstance(data, list):
            data = [normalize_record(r) for r in data]
        write_json(data, DATA_DIR / "policy" / "corridor_policy.json")
    # Per-country files
    for code in ("BEN", "CIV", "GHA", "NGA", "TGO"):
        country_files = sorted(src.glob(f"{code}_policy_data_*.json"))
        if country_files:
            data = load_json_safe(country_files[0])
            if isinstance(data, list):
                data = [normalize_record(r) for r in data]
            write_json(data, DATA_DIR / "policy" / f"{code}_policy.json")


def import_stakeholders():
    """Import stakeholder registry."""
    print("\n=== Stakeholders ===")
    src = DOWNLOADS / "stakeholders" / "stakeholders" / "combined"
    json_files = sorted(src.glob("ALL_stakeholders_*.json"))
    if not json_files:
        print("  SKIP: no ALL_stakeholders JSON found")
        return
    data = load_json_safe(json_files[0])
    if isinstance(data, dict) and "stakeholders" in data:
        records = data["stakeholders"]
    elif isinstance(data, list):
        records = data
    else:
        records = [data]
    records = [normalize_record(r) for r in records]
    write_json(records, DATA_DIR / "stakeholders_registry" / "stakeholders.json")


def import_tourism():
    """Import tourism data."""
    print("\n=== Tourism ===")
    src = DOWNLOADS / "tourism_data_20260216_195041"
    json_files = sorted(src.glob("tourism_data_*.json"))
    if not json_files:
        print("  SKIP: no tourism JSON found")
        return
    data = load_json_safe(json_files[0])
    if isinstance(data, list):
        data = [normalize_record(r) for r in data]
    write_json(data, DATA_DIR / "tourism" / "tourism.json")


def import_agriculture():
    """Import enriched agriculture data."""
    print("\n=== Agriculture (enriched) ===")
    src = DOWNLOADS / "agriculture_data" / "agriculture_data"
    json_files = sorted(src.glob("agriculture_data_*.json"))
    if not json_files:
        print("  SKIP: no agriculture JSON found")
        return
    data = load_json_safe(json_files[0])
    if isinstance(data, list):
        data = [normalize_record(r) for r in data]
    write_json(data, DATA_DIR / "agriculture_enriched" / "agriculture.json")


def import_infrastructure():
    """Import enriched infrastructure data (roads summary, ports, power)."""
    print("\n=== Infrastructure (enriched) ===")
    src = DOWNLOADS / "infrastructureV2" / "infrastructureV2"
    out_dir = DATA_DIR / "infrastructure_enriched"

    # Ports CSV → JSON
    ports_files = sorted(src.glob("ports_*.csv"))
    if ports_files:
        records = load_csv_as_list(ports_files[0])
        records = [normalize_record(r) for r in records]
        write_json(records, out_dir / "ports.json")

    # Power CSV → JSON
    power_files = sorted(src.glob("power_*.csv"))
    if power_files:
        records = load_csv_as_list(power_files[0])
        records = [normalize_record(r) for r in records]
        write_json(records, out_dir / "power.json")

    # Roads CSV → pre-computed summary (NOT raw 46K rows)
    roads_files = sorted(src.glob("roads_*.csv"))
    if roads_files:
        print("  Computing roads summary from 46K+ rows...")
        rows = load_csv_as_list(roads_files[0])

        # Normalize
        for r in rows:
            if "region" in r:
                r["region"] = normalize_country(r["region"])

        # Compute summaries
        by_country = defaultdict(lambda: {
            "total_segments": 0,
            "total_length_km": 0.0,
            "condition": Counter(),
            "surface": Counter(),
            "road_type": Counter(),
            "toll_segments": 0,
            "speed_sum": 0.0,
            "speed_count": 0,
        })

        for r in rows:
            country = r.get("region", "UNKNOWN")
            stats = by_country[country]
            stats["total_segments"] += 1
            try:
                stats["total_length_km"] += float(r.get("length_km", 0) or 0)
            except (ValueError, TypeError):
                pass
            cond = (r.get("condition") or "unknown").lower()
            stats["condition"][cond] += 1
            surf = (r.get("surface") or "unknown").lower()
            stats["surface"][surf] += 1
            rtype = (r.get("road_type") or "unknown").lower()
            stats["road_type"][rtype] += 1
            toll = (r.get("toll_required") or "").lower()
            if toll in ("yes", "true", "1"):
                stats["toll_segments"] += 1
            try:
                speed = float(r.get("average_speed_kph", 0) or 0)
                if speed > 0:
                    stats["speed_sum"] += speed
                    stats["speed_count"] += 1
            except (ValueError, TypeError):
                pass

        summary = {
            "total_segments": len(rows),
            "total_length_km": round(sum(s["total_length_km"] for s in by_country.values()), 1),
            "by_country": {},
        }

        for country, stats in sorted(by_country.items()):
            avg_speed = round(stats["speed_sum"] / stats["speed_count"], 1) if stats["speed_count"] > 0 else None
            summary["by_country"][country] = {
                "total_segments": stats["total_segments"],
                "total_length_km": round(stats["total_length_km"], 1),
                "average_speed_kph": avg_speed,
                "toll_segments": stats["toll_segments"],
                "condition": dict(stats["condition"]),
                "surface": dict(stats["surface"]),
                "road_type": dict(stats["road_type"]),
            }

        write_json(summary, out_dir / "roads_summary.json")


def import_macro():
    """Import enriched macro-economic data."""
    print("\n=== Macro (enriched) ===")
    src = DOWNLOADS / "macro economic data" / "output"
    json_files = sorted(src.glob("ALL_macro_*.json"))
    if not json_files:
        # Try CSV
        csv_files = sorted(src.glob("ALL_macro_*.csv"))
        if csv_files:
            records = load_csv_as_list(csv_files[0])
            records = [normalize_record(r) for r in records]
            write_json(records, DATA_DIR / "macro_enriched" / "macro.json")
        else:
            print("  SKIP: no macro data found")
        return
    data = load_json_safe(json_files[0])
    if isinstance(data, list):
        data = [normalize_record(r) for r in data]
    write_json(data, DATA_DIR / "macro_enriched" / "macro.json")


def import_projects():
    """Import enriched projects data (with encoding fix)."""
    print("\n=== Projects (enriched) ===")
    src = DOWNLOADS / "Project Specific Data" / "output"
    json_files = sorted(src.glob("ALL_projects_*.json"))
    if not json_files:
        print("  SKIP: no projects JSON found")
        return
    # Use safe loader (handles Windows-1252)
    data = load_json_safe(json_files[0])
    if isinstance(data, dict) and "projects" in data:
        records = data["projects"]
    elif isinstance(data, list):
        records = data
    else:
        records = [data]
    records = [normalize_record(r) for r in records]
    write_json(records, DATA_DIR / "projects_enriched" / "projects.json")


def update_freshness():
    """Add entries to freshness.json for new datasets."""
    print("\n=== Updating freshness.json ===")
    freshness_path = DATA_DIR / "freshness.json"
    if freshness_path.exists():
        with open(freshness_path, "r") as f:
            freshness = json.load(f)
    else:
        freshness = {}

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()

    new_entries = {
        "manufacturing": "companies.json",
        "policy": "corridor_policy.json",
        "stakeholders_registry": "stakeholders.json",
        "tourism": "tourism.json",
        "agriculture_enriched": "agriculture.json",
        "infrastructure_enriched": "roads_summary.json, ports.json, power.json",
        "macro_enriched": "macro.json",
        "projects_enriched": "projects.json",
    }

    for key, files in new_entries.items():
        freshness[key] = {
            "pulled_at": now,
            "source": "static_import_from_downloads_corridors",
            "files": files,
        }

    with open(freshness_path, "w") as f:
        json.dump(freshness, f, indent=2)
    print(f"  -> Updated {freshness_path}")


def main():
    print("=" * 60)
    print("Importing Corridor datasets into monorepo")
    print(f"Source: {DOWNLOADS}")
    print(f"Target: {DATA_DIR}")
    print("=" * 60)

    import_manufacturing()
    import_policy()
    import_stakeholders()
    import_tourism()
    import_agriculture()
    import_infrastructure()
    import_macro()
    import_projects()
    update_freshness()

    print("\n" + "=" * 60)
    print("Import complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
