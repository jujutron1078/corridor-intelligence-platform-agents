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

**What it does:** Identifies **relevant Development Finance Institutions (DFIs)** based on geography, sector, and development impact. It matches project characteristics against the mandates of 20+ institutions (e.g. AfDB, World Bank, EU Global Gateway). It accepts corridor countries, project sectors (e.g. Transmission, Digital), and development impact metrics from the Economic Impact agent and returns eligible institutions with relevance scores and a recommended engagement sequence.

**When to use:** At the start of financing design to know which DFIs to approach and in what order.

**Key concepts:** DFI mandates, eligibility (country, sector, ticket size, impact), and engagement sequencing to maximize fit and speed.

---

### 2. `generate_financing_scenarios`

**What it does:** Generates **20–30 blended finance structures** by combining grants, concessional loans, and commercial debt in various ratios to find an optimal **Weighted Average Cost of Capital (WACC)**. It accepts total CAPEX (from the Infrastructure agent), target equity IRR, and maximum commercial debt ratio, and returns the scenarios generated, the recommended scenario (breakdown of grants, concessional, commercial, equity, and WACC), and a summary message.

**When to use:** To explore the mix of grant/concessional/commercial/equity that makes the project financeable at target returns.

**Key concepts:** Blended finance, WACC, concessional vs commercial debt, grant component, equity IRR target.

---

### 3. `build_financial_model`

**What it does:** Builds a detailed **Discounted Cash Flow (DCF)** model. It calculates project IRR, equity IRR, NPV, and **Debt Service Coverage Ratio (DSCR)** over a 20–30 year lifecycle. It accepts revenue projections (e.g. from Opportunity Identification), CAPEX/OPEX (from Infrastructure), and the chosen financing structure from the financing scenarios tool. It returns equity IRR, project IRR, NPV, minimum DSCR, payback period, and status.

**When to use:** After selecting a financing scenario, to validate that the structure is viable and to produce covenant and reporting metrics.

**Key concepts:** DCF, project vs equity IRR, NPV, DSCR, debt service, payback.

---

### 4. `perform_risk_and_sensitivity_analysis`

**What it does:** Runs **sensitivity analysis and Monte Carlo simulations**. It identifies critical assumptions and can produce tornado-style outputs showing the impact of variables on IRR. It accepts financial model data from `build_financial_model` and optional variable variances (e.g. CAPEX, revenue, interest rate). It returns Monte Carlo results (e.g. probability of IRR above 12%, P50/P90 IRR), critical risks, and a summary message.

**When to use:** To stress-test the financial model and communicate key risks to lenders and equity.

**Key concepts:** Sensitivity analysis, Monte Carlo, tornado diagram, P50/P90, key driver identification.

---

### 5. `optimize_debt_terms`

**What it does:** Determines **optimal debt tenors, grace periods, and amortization schedules**. It aligns the repayment profile with the project’s cash flow ramp-up to maximize DSCR. It accepts total debt amount and annual cash flow available for debt service (CFADS) and returns optimized terms: tenor (years), grace period, concessional and commercial interest rates, and a summary message.

**When to use:** When the base financing structure is set but you need to tune repayment to match construction and ramp-up.

**Key concepts:** Tenor, grace period, amortization profile, CFADS, DSCR alignment.

---

### 6. `model_credit_enhancement`

**What it does:** Models **guarantees, political risk insurance (PRI), and other risk mitigation instruments**. It calculates the cost vs benefit of enhancements from providers such as MIGA or GuarantCo. It accepts the “gap” in bankability (amount of risk reduction needed for commercial lenders) and returns an enhancement plan (instrument, provider, cost in bps, commercial debt reduction), final WACC impact, and a summary message.

**When to use:** When the project needs partial risk guarantees or insurance to attract commercial debt or improve terms.

**Key concepts:** Credit enhancement, PRI, partial risk guarantee, WACC impact, commercial debt capacity.

---

## Typical Workflow

1. **DFI matching:** Use `match_dfi_institutions` with corridor and impact data to get a shortlist and engagement order.
2. **Scenario generation:** Use `generate_financing_scenarios` with CAPEX and return targets to get a recommended blended structure.
3. **Model build:** Use `build_financial_model` with revenues, CAPEX/OPEX, and chosen scenario to get IRR, NPV, DSCR.
4. **Risk:** Use `perform_risk_and_sensitivity_analysis` to identify and quantify key risks.
5. **Debt tuning:** Use `optimize_debt_terms` to align repayments with cash flow.
6. **Bankability gap:** If needed, use `model_credit_enhancement` to design guarantees/insurance and assess WACC impact.
