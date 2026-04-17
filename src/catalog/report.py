"""
Data availability report generator — produces a Markdown report.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.catalog.catalog import get_catalog, SourceType, ValidationStatus
from src.shared.pipeline.utils import OUTPUTS_DIR, ensure_dir

logger = logging.getLogger("corridor.catalog.report")

# ── Known data gaps ──────────────────────────────────────────────────────────

KNOWN_GAPS = [
    {
        "issue": "WorldPop stops at 2020",
        "impact": "No gridded population data after 2020",
        "workaround": "Use GHSL built-up surface (2020 epoch) + Google Open Buildings as proxy",
    },
    {
        "issue": "OSM secondary roads patchy in Benin/Togo",
        "impact": "Road network analysis incomplete in middle corridor segment",
        "workaround": "Supplement with GRIP global roads dataset + USGS Africa roads layer",
    },
    {
        "issue": "Mapillary street imagery sparse outside Lagos/Accra/Abidjan",
        "impact": "Limited ground-truth visual data for rural corridor segments",
        "workaround": "Use high-resolution satellite imagery + Claude Vision for rural analysis",
    },
    {
        "issue": "No real-time port activity data",
        "impact": "Cannot track live shipping/cargo volumes",
        "workaround": "Use VIIRS nightlights as proxy for port activity (nighttime = active operations)",
    },
    {
        "issue": "Sentinel-2 cloud cover May-October (wet season)",
        "impact": "Optical imagery unreliable during rainy season",
        "workaround": "Use Sentinel-1 SAR (all-weather radar) for wet season analysis",
    },
    {
        "issue": "Policy documents require manual collection",
        "impact": "Trade policy analysis depends on manual PDF collection",
        "workaround": "Not automated — requires manual sourcing from government websites, ECOWAS portal",
    },
]


def generate_report(
    validation_results: dict[str, Any] | None = None,
) -> str:
    """Generate a Markdown data availability report."""
    catalog = get_catalog()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        "# Lagos-Abidjan Corridor Intelligence Platform",
        "## Data Availability Report",
        f"\n*Generated: {now}*\n",
        "---\n",
    ]

    # ── Summary ──────────────────────────────────────────────────────────────
    if validation_results:
        summary = validation_results.get("summary", {})
        lines.append("### Summary\n")
        lines.append(f"| Metric | Count |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Total sources | {summary.get('total', 'N/A')} |")
        lines.append(f"| Validated | {summary.get('validated', 'N/A')} |")
        lines.append(f"| Partial | {summary.get('partial', 'N/A')} |")
        lines.append(f"| Missing | {summary.get('missing', 'N/A')} |")
        lines.append("")

    # ── By source type ───────────────────────────────────────────────────────
    for source_type in SourceType:
        sources = [s for s in catalog if s.source_type == source_type]
        if not sources:
            continue

        lines.append(f"### {source_type.value.upper()} Data Sources\n")
        lines.append("| Name | Resolution | Temporal Range | Tier | Status | Notes |")
        lines.append("|------|-----------|----------------|------|--------|-------|")

        for ds in sources:
            status_icon = {
                ValidationStatus.VALIDATED: "OK",
                ValidationStatus.PARTIAL: "PARTIAL",
                ValidationStatus.MISSING: "MISSING",
                ValidationStatus.MANUAL: "MANUAL",
                ValidationStatus.UNKNOWN: "?",
            }.get(ds.status, "?")

            lines.append(
                f"| {ds.name} | {ds.resolution} | {ds.temporal_range} | "
                f"{ds.tier} | {status_icon} | {ds.notes} |"
            )

        lines.append("")

    # ── Known gaps ───────────────────────────────────────────────────────────
    lines.append("### Known Data Gaps & Workarounds\n")
    lines.append("| Issue | Impact | Workaround |")
    lines.append("|-------|--------|------------|")
    for gap in KNOWN_GAPS:
        lines.append(f"| {gap['issue']} | {gap['impact']} | {gap['workaround']} |")
    lines.append("")

    # ── Validation details ───────────────────────────────────────────────────
    if validation_results:
        for section_name in ["gee", "osm", "mineral", "trade"]:
            section = validation_results.get(section_name, {})
            if not section:
                continue
            lines.append(f"### {section_name.upper()} Validation Details\n")
            lines.append("| Source | Status | Details |")
            lines.append("|--------|--------|---------|")
            for name, info in section.items():
                status = info.get("status", "unknown")
                details = info.get("error", "") or f"Count: {info.get('count', 'N/A')}"
                lines.append(f"| {name} | {status} | {details} |")
            lines.append("")

    return "\n".join(lines)


def save_report(
    validation_results: dict[str, Any] | None = None,
    output_path: Path | None = None,
) -> Path:
    """Generate and save the report."""
    report_text = generate_report(validation_results)
    output_path = output_path or (ensure_dir(OUTPUTS_DIR) / "data_availability_report.md")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_text)

    logger.info("Report saved: %s", output_path)
    return output_path
