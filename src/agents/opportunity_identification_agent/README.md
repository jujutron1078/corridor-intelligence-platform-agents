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

**What it does:** Identifies **specific commercial identities and economic sectors** for infrastructure detections. It cross-references GPS coordinates (e.g. from the Geospatial agent’s infrastructure detection) with national mining cadastres, industrial registries, and trade databases. It returns a **catalog of anchor loads** with company names and sectors.

**When to use:** After infrastructure/feature detection has produced coordinates; use to attach real entities and sectors to those points for demand and bankability.

**Key concepts:** Anchor load = identifiable demand node (mine, factory, port, etc.); entity resolution links coordinates to registries.

---

### 2. `calculate_current_demand`

**What it does:** Calculates the **current electricity demand (MW)** for each identified anchor load. It uses sector-specific energy intensity benchmarks and facility size to estimate load requirements.

**When to use:** After anchor loads are cataloged; use to get baseline demand for financial modeling and grid sizing.

**Key concepts:** Energy intensity (MWh per unit output), facility size, sector (mining, manufacturing, agro, etc.).

---

### 3. `assess_bankability`

**What it does:** Scores anchor loads by **creditworthiness, off-take willingness, and payment capacity**. It estimates the likelihood of a facility signing a long-term infrastructure (e.g. power) contract and honoring it.

**When to use:** To rank which anchor loads are most likely to convert into bankable off-take and to flag weak credits.

**Key concepts:** Bankability, off-take agreement, credit risk, payment capacity, contract readiness.

---

### 4. `model_growth_trajectory`

**What it does:** Projects **demand growth over a 20-year horizon** based on economic zone expansion plans, national GDP forecasts, and sector-specific growth trends.

**When to use:** To produce revenue and demand projections for the financial model and for phasing.

**Key concepts:** Growth rate, economic zones, sector trends, 20-year horizon.

---

### 5. `economic_gap_analysis`

**What it does:** Identifies **high-potential areas underserved by current infrastructure**. It overlays demand hotspots with existing grid/road layers to find critical gaps.

**When to use:** To justify where the corridor should go and which gaps it addresses.

**Key concepts:** Demand hotspot, existing network, gap = unmet demand or poor supply quality.

---

### 6. `prioritize_opportunities`

**What it does:** **Ranks opportunities** by revenue potential, development impact, and strategic value. It identifies the **top 10–15 anchor loads** (or segments) for a phased investment strategy.

**When to use:** After demand, bankability, and gap analysis; use to produce the shortlist for Phase 1 and subsequent phases.

**Key concepts:** Prioritization criteria (revenue, impact, risk), phased portfolio, strategic value.

---

## Typical Workflow

1. **Anchor catalog:** Use `scan_anchor_loads` to attach entities and sectors to detected infrastructure points.
2. **Baseline demand:** Use `calculate_current_demand` for current MW per anchor.
3. **Bankability:** Use `assess_bankability` to score off-take likelihood and credit.
4. **Growth:** Use `model_growth_trajectory` for 20-year demand/revenue projection.
5. **Gaps:** Use `economic_gap_analysis` to map underserved demand and justify corridor.
6. **Ranking:** Use `prioritize_opportunities` to get the top 10–15 for phasing and investment sequencing.

Outputs (anchor list, demand, revenue projections, priorities) feed into Financing, Infrastructure, and Economic Impact agents.
