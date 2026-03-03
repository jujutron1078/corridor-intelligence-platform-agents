# Opportunity Identification Agent

This agent identifies and prioritizes investment opportunities along the corridor. It links geospatial detections to real commercial entities (anchor loads), estimates current and future demand, assesses bankability, performs economic gap analysis, and ranks opportunities for phased investment.

---

## Shared Tools (Platform-Wide)

All agents use these common tools:

| Tool | Purpose |
|------|--------|
| **think_tool** | Step-by-step reasoning and documentation of assumptions. |
| **write_todos** | Structured task list for multi-step workflows. |

---

## Domain Tools

### 1. `scan_anchor_loads`

**What it does:** Identifies **specific commercial identities and economic sectors** along the corridor. It cross-references the corridor zone with national mining cadastres, industrial registries, and trade databases. It returns a **catalog of anchor loads** with company names and sectors.

**When to use:** As the entry point to build the anchor catalog for a corridor; no prior infrastructure detections required. Use to get real entities and sectors for demand and bankability.

**Key concepts:** Anchor load = identifiable demand node (mine, factory, port, etc.); entity resolution links coordinates to registries.

| **Input** | **Output** |
|-----------|------------|
| `sectors` *(optional)* — Sectors to cross-reference. Default: `["energy", "mining", "agriculture", "industrial", "digital"]`. | `status` — Scan status (e.g. `"Scanning Complete"`). |
| | `total_anchors_identified` — Count of anchors found. |
| | `anchor_catalog` — List of `{ anchor_id, name, sector, sub_sector, country, coords }`. |
| | `message` — Summary message. |

---

### 2. `calculate_current_demand`

**What it does:** Calculates the **current electricity demand (MW)** for each identified anchor load. It uses sector-specific energy intensity benchmarks and facility size to estimate load requirements.

**When to use:** After anchor loads are cataloged; use to get baseline demand for financial modeling and grid sizing.

**Key concepts:** Energy intensity (MWh per unit output), facility size, sector (mining, manufacturing, agro, etc.).

| **Input** | **Output** |
|-----------|------------|
| `anchor_load_ids` *(required)* — List of IDs from the anchor load scanner. | `total_current_mw` — Aggregated current demand (MW). |
| `resource_type` *(optional)* — Type of demand: `"electricity"` or `"water"`. Default: `"electricity"`. | `demand_profiles` — List of `{ anchor_id, current_mw, load_factor, reliability_class }`. |
| | `message` — Summary message. |

---

### 3. `assess_bankability`

**What it does:** Scores anchor loads by **creditworthiness, off-take willingness, and payment capacity**. It estimates the likelihood of a facility signing a long-term infrastructure (e.g. power) contract and honoring it.

**When to use:** To rank which anchor loads are most likely to convert into bankable off-take and to flag weak credits.

**Key concepts:** Bankability, off-take agreement, credit risk, payment capacity, contract readiness.

| **Input** | **Output** |
|-----------|------------|
| `anchor_load_ids` *(required)* — List of anchor/company IDs to score. | `corridor_average_score` — Average bankability score for the corridor (0–1). |
| | `tier_summary` — `{ tier_1_count, tier_2_count, tier_3_count }` (bankable / viable with enhancement / high risk). |
| | `bankability_scores` — List of `{ anchor_id, score, category, offtake_willingness, rationale }` (e.g. Tier 1/2/3). |
| | `message` — Summary message. |

---

### 4. `model_growth_trajectory`

**What it does:** Projects **demand growth over a 20-year horizon** based on economic zone expansion plans, national GDP forecasts, and sector-specific growth trends.

**When to use:** To produce revenue and demand projections for the financial model and for phasing.

**Key concepts:** Growth rate, economic zones, sector trends, 20-year horizon.

| **Input** | **Output** |
|-----------|------------|
| `anchor_load_ids` *(required)* — List of anchor IDs to project. | `projection_summary` — Text summary of aggregate demand growth (e.g. “238% over 20 years”). |
| `horizon_years` *(optional)* — Forecast period in years. Default: `20`. | `aggregate_trajectory` — `{ current_mw, year_5_mw, year_10_mw, year_20_mw, overall_growth_pct }`. |
| | `trajectories` — List of `{ anchor_id, current_mw, year_5_mw, year_20_mw, cagr, growth_driver }`. |
| | `message` — Summary message. |

---

### 5. `economic_gap_analysis`

**What it does:** Identifies **high-potential areas underserved by current infrastructure**. It overlays demand hotspots with existing grid/road layers to find critical gaps.

**When to use:** To justify where the corridor should go and which gaps it addresses.

**Key concepts:** Demand hotspot, existing network, gap = unmet demand or poor supply quality.

| **Input** | **Output** |
|-----------|------------|
| `corridor_id` *(required)* — ID of the study area/corridor. | `gaps_found` — Number of critical gaps identified. |
| | `total_unmet_demand_mw` — Total unmet demand (MW) across all gaps. |
| | `gap_summary` — `{ transmission_gaps, agricultural_cold_spots, industrial_underservice }` (counts by type). |
| | `critical_gaps` — List of `{ gap_id, location, country_span, coords, unmet_demand_mw, gap_type, opportunity_type, nearest_substation_km, severity, anchors_affected, rationale, recommended_intervention, estimated_capex_usd_m, investment_priority }`. |
| | `message` — Summary message. |

---

### 6. `prioritize_opportunities`

**What it does:** **Ranks opportunities** by revenue potential, development impact, and strategic value. It identifies the **top 10–15 anchor loads** (or segments) for a phased investment strategy.

**When to use:** After demand, bankability, and gap analysis; use to produce the shortlist for Phase 1 and subsequent phases.

**Key concepts:** Prioritization criteria (revenue, impact, risk), phased portfolio, strategic value.

| **Input** | **Output** |
|-----------|------------|
| `anchor_catalog` *(required)* — Catalog (list of dicts) with demand and bankability data for each anchor. | `top_15_count` — Number of opportunities in the shortlist. |
| | `scoring_methodology` — `{ bankability_weight, demand_weight, regional_impact_weight, score_range }`. |
| | `priority_list` — List of `{ rank, id, name, sector, country, composite_score, score_breakdown, phase, current_mw, year_5_mw, rationale, recommended_action }` (e.g. top 15). |
| | `phased_roadmap` — `{ phase_1, phase_2 }` with anchor counts, MW, capex, and focus per phase. |
| | `recommendation` — Phasing recommendation (e.g. Phase 1 focus). |
| | `message` — Summary message. |

---

## Typical Workflow

1. **Anchor catalog:** Use `scan_anchor_loads` to build the catalog of entities and sectors along the corridor.
2. **Baseline demand:** Use `calculate_current_demand` for current MW per anchor.
3. **Bankability:** Use `assess_bankability` to score off-take likelihood and credit.
4. **Growth:** Use `model_growth_trajectory` for 20-year demand/revenue projection.
5. **Gaps:** Use `economic_gap_analysis` to map underserved demand and justify corridor.
6. **Ranking:** Use `prioritize_opportunities` to get the top 10–15 for phasing and investment sequencing.

Outputs (anchor list, demand, revenue projections, priorities) feed into Financing, Infrastructure, and Economic Impact agents.
