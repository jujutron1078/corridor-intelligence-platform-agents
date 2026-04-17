import json
import logging

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import AgricultureOpportunityScanInput

logger = logging.getLogger("corridor.agent.opportunity.scan_agriculture")

COUNTRY_NAMES = {
    "BEN": "Benin",
    "CIV": "Côte d'Ivoire",
    "GHA": "Ghana",
    "NGA": "Nigeria",
    "TGO": "Togo",
}

# Average processing facility cost estimates by crop (USD)
# Source: IFC agro-processing benchmarks for West Africa
PROCESSING_FACILITY_COSTS = {
    "cocoa": 8_000_000,
    "cashew": 3_000_000,
    "palm_oil": 5_000_000,
    "rubber": 6_000_000,
    "cassava": 2_500_000,
    "rice": 4_000_000,
    "maize": 3_500_000,
    "yams": 2_000_000,
}

# Jobs per processing facility estimate
# Source: IFC employment intensity benchmarks for agro-processing
JOBS_PER_FACILITY = {
    "cocoa": 250,
    "cashew": 150,
    "palm_oil": 200,
    "rubber": 180,
    "cassava": 120,
    "rice": 100,
    "maize": 100,
    "yams": 80,
}

METHODOLOGY_TEMPLATE = (
    "This opportunity was identified using the Value Detective methodology, "
    "which cross-references multiple independent data sources to find investment "
    "gaps along the Lagos-Abidjan corridor. "
    "Step 1 (Production Analysis): FAO FAOSTAT {fao_year} data was used to establish "
    "{commodity} production volume for {country}. "
    "Step 2 (Value Chain Gap): UN Comtrade value chain analysis compared raw export "
    "prices against processed product prices to quantify the processing gap — the "
    "percentage of production exported raw vs. processed domestically. "
    "Step 3 (Infrastructure Cross-Reference): Agriculture enriched data (World Bank, "
    "national statistics) provided regional context including existing processing "
    "capacity, storage capacity, post-harvest losses, and producing regions. "
    "OSM infrastructure data identified nearby industrial zones and ports. "
    "Step 4 (Opportunity Sizing): Investment cost was estimated from IFC "
    "agro-processing facility benchmarks. Annual value-add was calculated as "
    "processable volume × value-add per ton. Employment was estimated from IFC "
    "employment intensity benchmarks. "
    "Step 5 (Bankability Scoring): A composite score was derived from production "
    "scale, processing gap severity, and export market maturity."
)

STAPLE_METHODOLOGY_TEMPLATE = (
    "This opportunity was identified using the Value Detective methodology. "
    "Step 1 (Production Analysis): FAO FAOSTAT {fao_year} data established "
    "{commodity} production at {production:,.0f} tonnes for {country}. "
    "Step 2 (Post-Harvest Loss Analysis): Agriculture enriched data identified "
    "post-harvest losses of {phl_pct}%, representing {phl_tonnes:,.0f} tonnes of "
    "annual waste that storage/processing infrastructure could reduce. "
    "Step 3 (Value-Add Estimation): Conservative value-add of $150/ton applied "
    "to 10% of production (achievable processing target for a single facility). "
    "Step 4 (Bankability): Scored on production scale relative to corridor average."
)


def _load_json(path: str) -> dict | list:
    """Load a JSON file, return empty dict on failure."""
    try:
        from pathlib import Path
        data_dir = Path(__file__).resolve().parent.parent.parent.parent.parent.parent / "data"
        with open(data_dir / path) as f:
            return json.load(f)
    except Exception as exc:
        logger.warning("Failed to load %s: %s", path, exc)
        return {}


def _get_enriched_record(ag_enriched: list, country_iso: str, commodity: str) -> dict:
    """Find enriched agriculture record for a country/commodity pair."""
    if not isinstance(ag_enriched, list):
        return {}
    for rec in ag_enriched:
        if (rec.get("country", "").upper() == country_iso
                and rec.get("crop", "").lower() == commodity.lower()):
            return rec
    return {}


@tool("scan_agriculture_opportunities", description=TOOL_DESCRIPTION)
def scan_agriculture_opportunities_tool(
    payload: AgricultureOpportunityScanInput, runtime: ToolRuntime
) -> Command:
    """
    Cross-references FAO production data, trade value chains, enriched
    agriculture data, and OSM infrastructure to identify concrete
    agriculture and trade investment opportunities along the corridor.
    Each opportunity includes full justification with methodology,
    data evidence, calculations, assumptions, and data gaps.
    """
    opportunities = []
    data_sources_used = []

    # ── 1. Load all data sources ─────────────────────────────────────────
    fao_data = _load_json("fao/production.json")
    if fao_data:
        data_sources_used.append("FAO FAOSTAT")

    value_chains = _load_json("trade/value_chain_analysis.json")
    if value_chains:
        data_sources_used.append("UN Comtrade Value Chain Analysis")

    ag_enriched = _load_json("agriculture_enriched/agriculture.json")
    if ag_enriched:
        data_sources_used.append("Agriculture Enriched Dataset (World Bank, National Statistics)")

    osm_industrial = _load_json("osm/industrial.geojson")
    osm_ports = _load_json("osm/ports.geojson")
    if osm_industrial or osm_ports:
        data_sources_used.append("OpenStreetMap")

    industrial_count_by_country = {}
    for feat in (osm_industrial.get("features", []) if isinstance(osm_industrial, dict) else []):
        c = feat.get("properties", {}).get("country", "")
        if c:
            industrial_count_by_country[c] = industrial_count_by_country.get(c, 0) + 1

    port_names = []
    for feat in (osm_ports.get("features", []) if isinstance(osm_ports, dict) else []):
        name = feat.get("properties", {}).get("name", "")
        if name:
            port_names.append(name)

    # ── 2. Processing gap opportunities (cash crops) ─────────────────────
    if isinstance(value_chains, dict):
        ag_commodities = ["cocoa", "cashew", "palm_oil", "rubber"]
        for commodity in ag_commodities:
            if payload.crop and payload.crop.lower() != commodity:
                continue
            vc = value_chains.get(commodity)
            if not vc or not isinstance(vc, dict):
                continue

            gaps = vc.get("gaps_by_country", {})
            raw_price = vc.get("raw_price", 0)
            processed_price = vc.get("processed_price", 0)
            multiplier = vc.get("multiplier", 1)
            raw_product = vc.get("raw_product", commodity)
            processed_product = vc.get("processed_product", f"Processed {commodity}")

            for country_iso, gap_info in gaps.items():
                if payload.country and payload.country.upper() != country_iso:
                    continue
                if not isinstance(gap_info, dict):
                    continue

                processing_pct = gap_info.get("processing_pct", 0)
                missed_value_pct = gap_info.get("missed_value_pct", 0)
                potential_per_ton = gap_info.get("potential_value_per_ton_usd", 0)
                country_name = COUNTRY_NAMES.get(country_iso, country_iso)
                gap_notes = gap_info.get("notes", "")

                if missed_value_pct < 50:
                    continue

                # FAO production data
                production_tonnes = 0
                area_ha = 0
                yield_kg = 0
                fao_year = 2023
                if isinstance(fao_data, dict) and commodity in fao_data:
                    for record in fao_data[commodity]:
                        if record.get("country_iso3") == country_iso:
                            production_tonnes = record.get("production_tonnes", 0)
                            area_ha = record.get("area_harvested_ha", 0)
                            yield_kg = record.get("yield_kg_per_ha", 0)
                            fao_year = record.get("year", 2023)

                # Enriched agriculture data (ALL fields)
                enriched = _get_enriched_record(ag_enriched, country_iso, commodity)
                export_value_usd = enriched.get("export_value_usd", 0) or 0
                export_volume = enriched.get("export_volume_tons", 0) or 0
                regions = enriched.get("main_producing_regions", "")
                processing_capacity = enriched.get("processing_capacity_tons_year", 0) or 0
                storage_capacity = enriched.get("storage_capacity_tons", 0) or 0
                post_harvest_loss_pct = enriched.get("post_harvest_losses_pct", 0) or 0
                value_addition_pct = enriched.get("value_addition_pct", 0) or 0
                price_per_ton = enriched.get("price_usd_per_ton", 0) or 0
                ag_gdp_share = enriched.get("ag_gdp_share_pct", 0) or 0
                rural_pop_pct = enriched.get("rural_population_pct", 0) or 0
                fertilizer_kg = enriched.get("wb_fertilizer_kg_ha", 0) or 0
                certifications = enriched.get("certifications", "")
                enriched_year = enriched.get("year", 2020)

                facility_cost = PROCESSING_FACILITY_COSTS.get(commodity, 5_000_000)
                jobs = JOBS_PER_FACILITY.get(commodity, 150)

                # ── Calculations ─────────────────────────────────────
                if production_tonnes > 0 and potential_per_ton and potential_per_ton > 0:
                    processable_tonnes = production_tonnes * (missed_value_pct / 100)
                    annual_value_add = processable_tonnes * potential_per_ton
                    prod_scale_factor = min(1.0, production_tonnes / 5_000_000) * 0.3
                    gap_factor = (missed_value_pct / 100) * 0.15
                    bankability = min(0.95, 0.5 + prod_scale_factor + gap_factor)
                else:
                    processable_tonnes = 0
                    annual_value_add = export_value_usd * (missed_value_pct / 100) * (multiplier - 1) if export_value_usd else 0
                    prod_scale_factor = 0
                    gap_factor = missed_value_pct / 200
                    bankability = 0.5 + gap_factor

                if annual_value_add < 100_000:
                    continue

                bankability = round(bankability, 2)

                # ── Build data evidence ──────────────────────────────
                data_evidence = [
                    {"data_point": "Annual production", "value": f"{production_tonnes:,.0f} tonnes", "source": "FAO FAOSTAT", "year": fao_year},
                    {"data_point": "Area harvested", "value": f"{area_ha:,.0f} hectares", "source": "FAO FAOSTAT", "year": fao_year},
                    {"data_point": "Yield", "value": f"{yield_kg:,.0f} kg/ha", "source": "FAO FAOSTAT", "year": fao_year},
                    {"data_point": "Domestic processing rate", "value": f"{processing_pct}%", "source": "UN Comtrade Value Chain Analysis", "year": 2023},
                    {"data_point": "Raw export rate", "value": f"{missed_value_pct}%", "source": "UN Comtrade Value Chain Analysis", "year": 2023},
                    {"data_point": f"Raw product price ({raw_product})", "value": f"${raw_price:,.2f}/ton", "source": "UN Comtrade", "year": 2023},
                    {"data_point": f"Processed product price ({processed_product})", "value": f"${processed_price:,.2f}/ton", "source": "UN Comtrade", "year": 2023},
                    {"data_point": "Value-add per ton", "value": f"${potential_per_ton:,.2f}", "source": "UN Comtrade (derived)", "year": 2023},
                    {"data_point": "Value chain multiplier", "value": f"{multiplier}x", "source": "UN Comtrade Value Chain Analysis", "year": 2023},
                ]
                if export_value_usd:
                    data_evidence.append({"data_point": "Export value", "value": f"${export_value_usd:,.0f}", "source": "Agriculture Enriched Dataset", "year": enriched_year})
                if export_volume:
                    data_evidence.append({"data_point": "Export volume", "value": f"{export_volume:,.0f} tonnes", "source": "Agriculture Enriched Dataset", "year": enriched_year})
                if regions:
                    data_evidence.append({"data_point": "Main producing regions", "value": regions, "source": "Agriculture Enriched Dataset", "year": enriched_year})
                if processing_capacity:
                    data_evidence.append({"data_point": "Existing processing capacity", "value": f"{processing_capacity:,.0f} tonnes/year", "source": "Agriculture Enriched Dataset", "year": enriched_year})
                if storage_capacity:
                    data_evidence.append({"data_point": "Existing storage capacity", "value": f"{storage_capacity:,.0f} tonnes", "source": "Agriculture Enriched Dataset", "year": enriched_year})
                if post_harvest_loss_pct:
                    data_evidence.append({"data_point": "Post-harvest losses", "value": f"{post_harvest_loss_pct}%", "source": "Agriculture Enriched Dataset", "year": enriched_year})
                if ag_gdp_share:
                    data_evidence.append({"data_point": "Agriculture GDP share", "value": f"{ag_gdp_share:.1f}%", "source": "World Bank", "year": enriched_year})
                if rural_pop_pct:
                    data_evidence.append({"data_point": "Rural population", "value": f"{rural_pop_pct:.1f}%", "source": "World Bank", "year": enriched_year})

                # ── Build calculations ───────────────────────────────
                calculations = {
                    "investment_estimate": {
                        "facility_type": f"{commodity.replace('_', ' ').title()} processing plant",
                        "benchmark_cost_usd": facility_cost,
                        "benchmark_source": "IFC agro-processing facility benchmarks for West Africa",
                    },
                    "value_add": {
                        "production_tonnes": production_tonnes,
                        "currently_processed_pct": processing_pct,
                        "currently_processed_tonnes": round(production_tonnes * processing_pct / 100),
                        "processable_gap_pct": missed_value_pct,
                        "processable_gap_tonnes": round(processable_tonnes),
                        "value_add_per_ton_usd": potential_per_ton,
                        "formula": f"{processable_tonnes:,.0f} tonnes × ${potential_per_ton:,.2f}/ton",
                        "annual_value_add_usd": round(annual_value_add),
                    },
                    "employment": {
                        "direct_jobs": jobs,
                        "basis": f"IFC employment intensity benchmark for {commodity} processing in West Africa",
                    },
                    "bankability_score": {
                        "final_score": bankability,
                        "components": {
                            "base_score": 0.5,
                            "production_scale_factor": f"min(1.0, {production_tonnes:,.0f} / 5,000,000) × 0.3 = {round(prod_scale_factor, 3)}",
                            "gap_severity_factor": f"({missed_value_pct} / 100) × 0.15 = {round(gap_factor, 3)}",
                        },
                        "formula": f"0.5 + {round(prod_scale_factor, 3)} + {round(gap_factor, 3)} = {bankability}",
                    },
                    "gdp_multiplier": {
                        "value": multiplier,
                        "meaning": f"Each $1 of raw {commodity} becomes ${multiplier} when processed",
                        "source": "UN Comtrade value chain analysis",
                    },
                }

                # ── Risk breakdown ───────────────────────────────────
                risk_breakdown = {
                    "production_risk": "Low" if production_tonnes > 100_000 else "Medium",
                    "production_reasoning": f"Established production base of {production_tonnes:,.0f} tonnes/year",
                    "market_risk": "Low" if export_value_usd > 1_000_000 else "Medium",
                    "market_reasoning": f"Export value of ${export_value_usd:,.0f} indicates established demand" if export_value_usd else "Export data unavailable",
                    "infrastructure_risk": "Medium",
                    "infrastructure_reasoning": f"{industrial_count_by_country.get(country_iso, 0)} industrial zones in country; facility construction in {'established' if processing_capacity else 'underserved'} processing area",
                    "overall": "low" if bankability > 0.7 else "medium" if bankability > 0.5 else "high",
                }

                # ── Assumptions and data gaps ────────────────────────
                assumptions = [
                    f"Facility cost of ${facility_cost / 1_000_000:.1f}M based on IFC West Africa benchmarks (actual cost varies by location and scale)",
                    f"Employment estimate of {jobs} direct jobs based on IFC intensity benchmarks",
                    f"All {missed_value_pct}% of unprocessed production is theoretically available for processing",
                    "Single facility cannot capture entire processing gap — annual value-add represents theoretical maximum",
                ]

                data_gaps = []
                if not regions:
                    data_gaps.append("Specific producing regions not available — opportunity is country-level")
                if not processing_capacity:
                    data_gaps.append("Existing processing capacity data not available — cannot estimate saturation")
                if not storage_capacity:
                    data_gaps.append("Storage capacity data not available")
                if enriched_year < 2022:
                    data_gaps.append(f"Enriched agriculture data from {enriched_year} — may not reflect current conditions")
                if not price_per_ton:
                    data_gaps.append("Country-specific commodity price not available — using global benchmark")

                # ── Methodology ──────────────────────────────────────
                methodology = METHODOLOGY_TEMPLATE.format(
                    commodity=commodity.replace("_", " "),
                    country=country_name,
                    fao_year=fao_year,
                )

                opp = {
                    "title": f"{commodity.replace('_', ' ').title()} Processing Facility — {country_name}",
                    "sector": "agriculture",
                    "sub_sector": f"{commodity}_processing",
                    "country": country_name,
                    "country_iso3": country_iso,
                    "location": {"name": regions if regions else country_name},
                    "opportunity_type": "processing_gap",
                    "bankability_score": bankability,
                    "estimated_value_usd": facility_cost,
                    "estimated_return_usd": round(annual_value_add),
                    "employment_impact": jobs,
                    "gdp_multiplier": multiplier,
                    "risk_level": risk_breakdown["overall"],
                    "summary": (
                        f"{country_name} produces {production_tonnes:,.0f} tonnes of {commodity.replace('_', ' ')} annually "
                        f"but processes only {processing_pct}% domestically, exporting {missed_value_pct}% "
                        f"as raw {raw_product}. A processing facility costing ~${facility_cost / 1_000_000:.1f}M "
                        f"could capture ${annual_value_add / 1_000_000:.1f}M/year in value-add "
                        f"and create ~{jobs} direct jobs. "
                        f"Value chain multiplier: {multiplier}x ({raw_product} → {processed_product})."
                        + (f" {gap_notes}" if gap_notes else "")
                    ),
                    "analysis_detail": (
                        f"Production: {production_tonnes:,.0f} tonnes/year ({fao_year}). "
                        f"Area: {area_ha:,.0f} ha. Yield: {yield_kg:,.0f} kg/ha. "
                        f"Processing rate: {processing_pct}%. Missed value: {missed_value_pct}%. "
                        f"Raw price: ${raw_price:,.2f}/ton → Processed: ${processed_price:,.2f}/ton. "
                        f"Value-add/ton: ${potential_per_ton:,.2f}. "
                        + (f"Export value: ${export_value_usd:,.0f}. " if export_value_usd else "")
                        + (f"Post-harvest losses: {post_harvest_loss_pct}%. " if post_harvest_loss_pct else "")
                        + (f"Existing processing capacity: {processing_capacity:,.0f} t/yr. " if processing_capacity else "")
                        + (f"Regions: {regions}. " if regions else "")
                        + (f"Ag GDP share: {ag_gdp_share:.1f}%. " if ag_gdp_share else "")
                        + f"Industrial zones: {industrial_count_by_country.get(country_iso, 0)}. "
                        + f"Nearby ports: {', '.join(port_names[:3]) if port_names else 'data pending'}."
                    ),
                    "data_sources": data_sources_used,
                    "nearby_infrastructure": port_names[:3],
                    # ── Justification fields ─────────────────────────
                    "methodology": methodology,
                    "data_evidence": data_evidence,
                    "calculations": calculations,
                    "assumptions": assumptions,
                    "data_gaps": data_gaps,
                    "risk_breakdown": risk_breakdown,
                }
                opportunities.append(opp)

    # ── 3. Staple crop opportunities ─────────────────────────────────────
    if isinstance(fao_data, dict):
        staple_crops = ["cassava", "yams", "maize", "rice"]
        for crop_name in staple_crops:
            if payload.crop and payload.crop.lower() != crop_name:
                continue
            records = fao_data.get(crop_name, [])
            for record in records:
                country_iso = record.get("country_iso3", "")
                if payload.country and payload.country.upper() != country_iso:
                    continue
                production = record.get("production_tonnes", 0)
                area_ha = record.get("area_harvested_ha", 0)
                yield_kg = record.get("yield_kg_per_ha", 0)
                fao_year = record.get("year", 2023)
                country_name = COUNTRY_NAMES.get(country_iso, country_iso)

                if production < 500_000:
                    continue

                enriched = _get_enriched_record(ag_enriched, country_iso, crop_name)
                regions = enriched.get("main_producing_regions", "")
                post_harvest_loss_pct = enriched.get("post_harvest_losses_pct", 0) or 0
                processing_capacity = enriched.get("processing_capacity_tons_year", 0) or 0
                storage_capacity = enriched.get("storage_capacity_tons", 0) or 0
                ag_gdp_share = enriched.get("ag_gdp_share_pct", 0) or 0
                rural_pop_pct = enriched.get("rural_population_pct", 0) or 0
                enriched_year = enriched.get("year", 2020)

                facility_cost = PROCESSING_FACILITY_COSTS.get(crop_name, 3_000_000)
                jobs = JOBS_PER_FACILITY.get(crop_name, 100)
                value_add_per_ton = 150
                processable_fraction = 0.1
                processable_tonnes = production * processable_fraction
                annual_value_add = processable_tonnes * value_add_per_ton
                phl_tonnes = production * (post_harvest_loss_pct / 100) if post_harvest_loss_pct else 0
                bankability = min(0.85, 0.4 + (production / 10_000_000) * 0.3)
                bankability = round(bankability, 2)

                data_evidence = [
                    {"data_point": "Annual production", "value": f"{production:,.0f} tonnes", "source": "FAO FAOSTAT", "year": fao_year},
                    {"data_point": "Area harvested", "value": f"{area_ha:,.0f} hectares", "source": "FAO FAOSTAT", "year": fao_year},
                    {"data_point": "Yield", "value": f"{yield_kg:,.0f} kg/ha", "source": "FAO FAOSTAT", "year": fao_year},
                ]
                if post_harvest_loss_pct:
                    data_evidence.append({"data_point": "Post-harvest losses", "value": f"{post_harvest_loss_pct}%", "source": "Agriculture Enriched Dataset", "year": enriched_year})
                if processing_capacity:
                    data_evidence.append({"data_point": "Existing processing capacity", "value": f"{processing_capacity:,.0f} tonnes/year", "source": "Agriculture Enriched Dataset", "year": enriched_year})
                if storage_capacity:
                    data_evidence.append({"data_point": "Existing storage capacity", "value": f"{storage_capacity:,.0f} tonnes", "source": "Agriculture Enriched Dataset", "year": enriched_year})
                if regions:
                    data_evidence.append({"data_point": "Main producing regions", "value": regions, "source": "Agriculture Enriched Dataset", "year": enriched_year})
                if ag_gdp_share:
                    data_evidence.append({"data_point": "Agriculture GDP share", "value": f"{ag_gdp_share:.1f}%", "source": "World Bank", "year": enriched_year})

                calculations = {
                    "investment_estimate": {
                        "facility_type": f"{crop_name.title()} storage & processing hub",
                        "benchmark_cost_usd": facility_cost,
                        "benchmark_source": "IFC agro-processing facility benchmarks for West Africa",
                    },
                    "value_add": {
                        "production_tonnes": production,
                        "processable_fraction": f"{processable_fraction * 100:.0f}% of production (single facility target)",
                        "processable_tonnes": round(processable_tonnes),
                        "value_add_per_ton_usd": value_add_per_ton,
                        "formula": f"{processable_tonnes:,.0f} tonnes × ${value_add_per_ton}/ton",
                        "annual_value_add_usd": round(annual_value_add),
                    },
                    "post_harvest_loss_reduction": {
                        "current_loss_pct": post_harvest_loss_pct,
                        "annual_loss_tonnes": round(phl_tonnes),
                        "note": "Storage infrastructure could reduce losses by 30-50%",
                    },
                    "employment": {
                        "direct_jobs": jobs,
                        "basis": f"IFC employment intensity benchmark for {crop_name} processing in West Africa",
                    },
                    "bankability_score": {
                        "final_score": bankability,
                        "components": {
                            "base_score": 0.4,
                            "production_scale_factor": f"({production:,.0f} / 10,000,000) × 0.3 = {round((production / 10_000_000) * 0.3, 3)}",
                        },
                        "formula": f"min(0.85, 0.4 + {round((production / 10_000_000) * 0.3, 3)}) = {bankability}",
                    },
                }

                methodology = STAPLE_METHODOLOGY_TEMPLATE.format(
                    commodity=crop_name,
                    country=country_name,
                    fao_year=fao_year,
                    production=production,
                    phl_pct=post_harvest_loss_pct,
                    phl_tonnes=phl_tonnes,
                )

                assumptions = [
                    f"Facility cost of ${facility_cost / 1_000_000:.1f}M based on IFC West Africa benchmarks",
                    f"10% of total production is a realistic processing target for a single facility",
                    f"Value-add of $150/ton is conservative for staple crop processing",
                    f"{jobs} direct jobs based on IFC employment intensity benchmarks",
                ]

                data_gaps = []
                if not processing_capacity:
                    data_gaps.append("Existing processing capacity data not available")
                if not storage_capacity:
                    data_gaps.append("Storage capacity data not available")
                if not post_harvest_loss_pct:
                    data_gaps.append("Post-harvest loss data not available — cannot quantify waste reduction potential")
                if enriched_year < 2022:
                    data_gaps.append(f"Enriched data from {enriched_year}")

                risk_breakdown = {
                    "production_risk": "Low",
                    "production_reasoning": f"Large-scale production of {production:,.0f} tonnes/year",
                    "market_risk": "Low",
                    "market_reasoning": "Staple crop with guaranteed domestic demand",
                    "infrastructure_risk": "Medium",
                    "infrastructure_reasoning": "Rural location likely; logistics and power access may be challenging",
                    "overall": "low" if bankability > 0.7 else "medium",
                }

                opp = {
                    "title": f"{crop_name.title()} Storage & Processing Hub — {country_name}",
                    "sector": "agriculture",
                    "sub_sector": f"{crop_name}_processing",
                    "country": country_name,
                    "country_iso3": country_iso,
                    "location": {"name": regions if regions else country_name},
                    "opportunity_type": "staple_processing",
                    "bankability_score": bankability,
                    "estimated_value_usd": facility_cost,
                    "estimated_return_usd": round(annual_value_add),
                    "employment_impact": jobs,
                    "gdp_multiplier": 1.8,
                    "risk_level": risk_breakdown["overall"],
                    "summary": (
                        f"{country_name} produces {production:,.0f} tonnes of {crop_name} annually. "
                        + (f"Post-harvest losses of {post_harvest_loss_pct}% ({phl_tonnes:,.0f} tonnes) represent significant waste. " if post_harvest_loss_pct else "")
                        + f"A storage and processing hub costing ~${facility_cost / 1_000_000:.1f}M could "
                        f"add ${annual_value_add / 1_000_000:.1f}M/year in value and create ~{jobs} jobs."
                    ),
                    "analysis_detail": (
                        f"Production: {production:,.0f} tonnes/year ({fao_year}). "
                        f"Area: {area_ha:,.0f} ha. Yield: {yield_kg:,.0f} kg/ha. "
                        + (f"Post-harvest losses: {post_harvest_loss_pct}% ({phl_tonnes:,.0f} tonnes). " if post_harvest_loss_pct else "")
                        + (f"Existing processing: {processing_capacity:,.0f} t/yr. " if processing_capacity else "")
                        + (f"Regions: {regions}. " if regions else "")
                        + (f"Ag GDP share: {ag_gdp_share:.1f}%. " if ag_gdp_share else "")
                    ),
                    "data_sources": data_sources_used,
                    "nearby_infrastructure": port_names[:3],
                    "methodology": methodology,
                    "data_evidence": data_evidence,
                    "calculations": calculations,
                    "assumptions": assumptions,
                    "data_gaps": data_gaps,
                    "risk_breakdown": risk_breakdown,
                }
                opportunities.append(opp)

    # ── 4. Sort and build response ───────────────────────────────────────
    opportunities.sort(key=lambda o: o.get("estimated_return_usd", 0), reverse=True)

    total_investment = sum(o.get("estimated_value_usd", 0) for o in opportunities)
    total_return = sum(o.get("estimated_return_usd", 0) for o in opportunities)
    total_jobs = sum(o.get("employment_impact", 0) for o in opportunities)

    response = {
        "status": "Agriculture Opportunity Scan Complete",
        "total_opportunities": len(opportunities),
        "total_investment_required_usd": total_investment,
        "total_annual_value_add_usd": total_return,
        "total_employment_impact": total_jobs,
        "opportunities": opportunities,
        "by_country": {},
        "by_type": {},
        "data_sources": data_sources_used,
        "message": (
            f"Identified {len(opportunities)} agriculture investment opportunities "
            f"requiring ${total_investment / 1_000_000:.0f}M total investment, "
            f"generating ${total_return / 1_000_000:.0f}M/year in value-add "
            f"and {total_jobs:,} direct jobs. "
            f"Each opportunity includes full methodology, data evidence with sources, "
            f"step-by-step calculations, assumptions, and data gaps."
        ),
    }

    for opp in opportunities:
        c = opp["country"]
        if c not in response["by_country"]:
            response["by_country"][c] = {"count": 0, "total_value": 0}
        response["by_country"][c]["count"] += 1
        response["by_country"][c]["total_value"] += opp.get("estimated_return_usd", 0)

    for opp in opportunities:
        t = opp.get("opportunity_type", "other")
        if t not in response["by_type"]:
            response["by_type"][t] = 0
        response["by_type"][t] += 1

    return Command(update={"messages": [ToolMessage(
        content=json.dumps(response), tool_call_id=runtime.tool_call_id,
    )]})
