# Realtime Monitoring Agent

This agent monitors corridor projects during implementation. It tracks construction progress, financial performance, anchor load realization, economic impact KPIs, detects implementation risks, and generates adaptive recommendations to keep the project on plan or respond to deviations.

---

## Shared Tools (Platform-Wide)

All agents use these common tools:

| Tool | Purpose |
|------|--------|
| **think_tool** | Step-by-step reasoning and documentation of assumptions. |
| **write_todos** | Structured task list for multi-step workflows. |

---

## Domain Tools

### 1. `track_construction_progress`

**What it does:** Tracks **physical progress against the baseline plan**. It monitors kilometers of transmission line strung, pylon foundations poured, substation commissioning milestones, and similar metrics. It calculates **percentage completion by phase**.

**When to use:** For construction dashboards, milestone reporting, and delay detection.

**Key concepts:** Baseline plan, physical % complete, milestones (foundations, stringing, commissioning).

---

### 2. `monitor_financial_performance`

**What it does:** Monitors **CAPEX vs. budget**, **revenue vs. projections**, and **financial covenants**. It calculates real-time **Debt Service Coverage Ratio (DSCR)** and **budget variance**.

**When to use:** For treasury and lender reporting, covenant compliance, and early warning on cost or revenue deviations.

**Key concepts:** CAPEX variance, revenue vs plan, DSCR, covenant breach risk.

---

### 3. `audit_anchor_load_realization`

**What it does:** Tracks **which anchor loads have materialized and are consuming power**. It compares actual demand growth vs. the 20-year projections to validate the commercial viability of the corridor.

**When to use:** To check if off-take assumptions are coming true and to update demand/revenue forecasts.

**Key concepts:** Anchor load realization, actual vs projected demand, commercial viability.

---

### 4. `track_economic_impact_kpis`

**What it does:** Monitors **actual jobs created, GDP contribution, and electrification progress**. It compares real-world impact results against the predictions made by the Economic Impact agent.

**When to use:** For development impact reporting to DFIs and government (jobs, GDP, access).

**Key concepts:** Jobs created, GDP contribution, electrification metrics, baseline vs actual impact.

---

### 5. `detect_implementation_risks`

**What it does:** Acts as an **early warning system** for cost overruns, delays, and stakeholder issues. It uses anomaly detection to flag risks before they become critical failures.

**When to use:** Continuously or on schedule, to surface emerging execution risks.

**Key concepts:** Anomaly detection, cost/delay/stakeholder risk, early warning.

---

### 6. `generate_adaptive_recommendations`

**What it does:** Suggests **corrective actions when deviations are detected**. It provides engineering, financial, or stakeholder tactics to bring the project back to baseline or to capitalize on early successes.

**When to use:** After risks or variances are identified; use to propose concrete next steps for project management.

**Key concepts:** Corrective actions, baseline recovery, opportunity capture (e.g. ahead-of-schedule demand).

---

## Typical Workflow

1. **Progress:** Use `track_construction_progress` for physical % complete and milestones.
2. **Financials:** Use `monitor_financial_performance` for CAPEX, revenue, DSCR, and covenants.
3. **Demand:** Use `audit_anchor_load_realization` to compare actual vs projected anchor load uptake.
4. **Impact:** Use `track_economic_impact_kpis` for jobs, GDP, electrification vs Economic Impact predictions.
5. **Risks:** Use `detect_implementation_risks` to flag overruns, delays, and stakeholder issues.
6. **Actions:** Use `generate_adaptive_recommendations` to propose engineering, financial, or stakeholder responses.

This agent closes the loop between planning (other agents) and execution, enabling ongoing course correction and impact verification.
