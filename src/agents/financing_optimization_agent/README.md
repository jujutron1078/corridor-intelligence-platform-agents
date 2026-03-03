# Financing Optimization Agent

This agent designs and optimizes financing structures for corridor infrastructure. It matches projects to Development Finance Institutions (DFIs), generates blended finance scenarios, builds financial models, runs risk and sensitivity analysis, optimizes debt terms, and models credit enhancement to improve bankability and cost of capital.

---

## Shared Tools (Platform-Wide)

All agents use these common tools:

| Tool | Purpose |
|------|--------|
| **think_tool** | Step-by-step reasoning and documentation of assumptions. |
| **write_todos** | Structured task list for multi-step workflows. |

---

## Domain Tools

### 1. `match_dfi_institutions`

**What it does:** Identifies **relevant Development Finance Institutions (DFIs)** based on geography, sector, and development impact. It matches project characteristics against the mandates of 20+ institutions (e.g. AfDB, World Bank, EU Global Gateway). It returns eligible institutions with relevance scores and a recommended engagement sequence.

**When to use:** At the start of financing design to know which DFIs to approach and in what order.

**Key concepts:** DFI mandates, eligibility (country, sector, ticket size, impact), and engagement sequencing to maximize fit and speed.

**Input:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `corridor_countries` | `List[str]` | Yes | Countries involved (e.g., Ghana, Nigeria). |
| `sectors` | `List[str]` | Yes | Project sectors (e.g., Transmission, Digital). |
| `development_impact_metrics` | `Dict` | Yes | Key impact stats from the Economic Impact agent. |

**Output:**

| Field | Type | Description |
|-------|------|-------------|
| `eligible_institutions` | `List[object]` | Each item: `name`, `focus`, `relevance` (0–1). |
| `engagement_sequence` | `List[str]` | Recommended order of approach (e.g. "Approach AfDB for anchor concessionality"). |
| `message` | `str` | Summary of matching result. |

---

### 2. `generate_financing_scenarios`

**What it does:** Generates **20–30 blended finance structures** by combining grants, concessional loans, and commercial debt in various ratios to find an optimal **Weighted Average Cost of Capital (WACC)**. It returns the scenarios generated, the recommended scenario (breakdown and WACC), and a summary message.

**When to use:** To explore the mix of grant/concessional/commercial/equity that makes the project financeable at target returns.

**Key concepts:** Blended finance, WACC, concessional vs commercial debt, grant component, equity IRR target.

**Input:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `total_capex` | `float` | Yes | CAPEX from the Infrastructure agent. |
| `target_equity_irr` | `float` | No (default: 0.14) | Target return for equity investors. |
| `max_commercial_debt_ratio` | `float` | No (default: 0.4) | Maximum ceiling for high-interest debt. |

**Output:**

| Field | Type | Description |
|-------|------|-------------|
| `scenarios_generated` | `int` | Number of blended structures generated (e.g. 25). |
| `recommended_scenario` | `object` | `grants_usd`, `concessional_loans_usd`, `commercial_debt_usd`, `equity_usd`, `wacc` (e.g. "6.2%"). |
| `message` | `str` | Summary and rationale for the recommended scenario. |

---

### 3. `build_financial_model`

**What it does:** Builds a detailed **Discounted Cash Flow (DCF)** model. It calculates project IRR, equity IRR, NPV, and **Debt Service Coverage Ratio (DSCR)** over a 20–30 year lifecycle. It returns equity IRR, project IRR, NPV, minimum DSCR, payback period, and status.

**When to use:** After selecting a financing scenario, to validate that the structure is viable and to produce covenant and reporting metrics.

**Key concepts:** DCF, project vs equity IRR, NPV, DSCR, debt service, payback.

**Input:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `revenue_projections` | `List[float]` | Yes | Annual revenues from Opportunity Identification agent. |
| `capex_opex_data` | `Dict` | Yes | Cost data from the Infrastructure agent. |
| `financing_structure` | `Dict` | Yes | The chosen scenario from `generate_financing_scenarios`. |

**Output:**

| Field | Type | Description |
|-------|------|-------------|
| `metrics` | `object` | `equity_irr`, `project_irr`, `net_present_value_usd`, `min_dscr`, `payback_period_years`. |
| `status` | `str` | Model readiness (e.g. "Investor-grade model ready"). |
| `message` | `str` | Summary of DCF results and target thresholds. |

---

### 4. `perform_risk_and_sensitivity_analysis`

**What it does:** Runs **sensitivity analysis and Monte Carlo simulations**. It identifies critical assumptions and can produce tornado-style outputs showing the impact of variables on IRR. It returns Monte Carlo results (e.g. probability of IRR above 12%, P50/P90 IRR), critical risks, and a summary message.

**When to use:** To stress-test the financial model and communicate key risks to lenders and equity.

**Key concepts:** Sensitivity analysis, Monte Carlo, tornado diagram, P50/P90, key driver identification.

**Input:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `financial_model_data` | `Dict` | Yes | Output from `build_financial_model`. |
| `variable_variances` | `Dict` | No (default: capex 15%, revenue 20%, interest_rate 2%) | Variance assumptions for sensitivity. |

**Output:**

| Field | Type | Description |
|-------|------|-------------|
| `monte_carlo_results` | `object` | `prob_irr_above_12_percent`, `p50_irr`, `p90_irr`. |
| `critical_risks` | `List[str]` | Top risks (e.g. "CAPEX overrun (>15%)", "Currency devaluation"). |
| `message` | `str` | Summary of risk analysis and probability of target returns. |

---

### 5. `optimize_debt_terms`

**What it does:** Determines **optimal debt tenors, grace periods, and amortization schedules**. It aligns the repayment profile with the project’s cash flow ramp-up to maximize DSCR. It returns optimized terms: tenor, grace period, concessional and commercial interest rates, and a summary message.

**When to use:** When the base financing structure is set but you need to tune repayment to match construction and ramp-up.

**Key concepts:** Tenor, grace period, amortization profile, CFADS, DSCR alignment.

**Input:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `debt_amount` | `float` | Yes | Total debt component. |
| `cash_flow_available_for_debt_service` | `List[float]` | Yes | Annual CFADS (Cash Flow Available for Debt Service). |

**Output:**

| Field | Type | Description |
|-------|------|-------------|
| `optimized_terms` | `object` | `tenor_years`, `grace_period_years`, `interest_rate_concessional`, `interest_rate_commercial`. |
| `message` | `str` | Summary of optimized terms and DSCR impact. |

---

### 6. `model_credit_enhancement`

**What it does:** Models **guarantees, political risk insurance (PRI), and other risk mitigation instruments**. It calculates the cost vs benefit of enhancements from providers such as MIGA or GuarantCo. It returns an enhancement plan (instrument, provider, cost in bps, commercial debt reduction), final WACC impact, and a summary message.

**When to use:** When the project needs partial risk guarantees or insurance to attract commercial debt or improve terms.

**Key concepts:** Credit enhancement, PRI, partial risk guarantee, WACC impact, commercial debt capacity.

**Input:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `gap_in_bankability` | `float` | Yes | Amount of risk reduction needed for commercial lenders. |

**Output:**

| Field | Type | Description |
|-------|------|-------------|
| `enhancement_plan` | `object` | `instrument`, `provider`, `cost_bps`, `commercial_debt_reduction_bps`. |
| `final_wacc_impact` | `str` | Change in WACC after enhancement (e.g. "-0.45%"). |
| `message` | `str` | Summary and recommendation (e.g. PCG to attract commercial banks). |

---

## Typical Workflow

1. **DFI matching:** Use `match_dfi_institutions` with corridor and impact data to get a shortlist and engagement order.
2. **Scenario generation:** Use `generate_financing_scenarios` with CAPEX and return targets to get a recommended blended structure.
3. **Model build:** Use `build_financial_model` with revenues, CAPEX/OPEX, and chosen scenario to get IRR, NPV, DSCR.
4. **Risk:** Use `perform_risk_and_sensitivity_analysis` to identify and quantify key risks.
5. **Debt tuning:** Use `optimize_debt_terms` to align repayments with cash flow.
6. **Bankability gap:** If needed, use `model_credit_enhancement` to design guarantees/insurance and assess WACC impact.
