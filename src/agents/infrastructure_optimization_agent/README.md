# Infrastructure Optimization Agent

This agent optimizes the technical and economic design of corridor infrastructure. It refines routes from the Geospatial agent into engineering alignments, quantifies colocation benefits, sizes voltage and capacity, optimizes substation placement, generates phasing strategies, and produces CAPEX/OPEX cost estimates.

---

## Shared Tools (Platform-Wide)

All agents use these common tools:

| Tool | Purpose |
|------|--------|
| **think_tool** | Step-by-step reasoning and documentation of assumptions. |
| **write_todos** | Structured task list for multi-step workflows. |

---

## Domain Tools

### 1. `refine_optimized_routes`

**What it does:** Calculates **least-cost paths within specific corridor proximity constraints**. It refines the broad paths from the Geospatial agent into precise engineering routes that stay within the legal highway right-of-way (or other corridor envelope).

**When to use:** When you have candidate routes from Geospatial and need alignment refined to respect RoW, colocation rules, or regulatory limits.

**Key concepts:** Right-of-way (RoW), colocation corridor, engineering alignment vs strategic path.

---

### 2. `quantify_colocation_benefits`

**What it does:** Models **CAPEX savings from infrastructure sharing**. It quantifies cost reductions from shared land clearing, access roads, and construction logistics when the power line is built alongside the highway (or other linear asset).

**When to use:** When comparing colocated vs standalone transmission to report savings and justify corridor approach.

**Key concepts:** Colocation = shared RoW and construction; savings in land, access, and mobilization.

---

### 3. `size_voltage_and_capacity`

**What it does:** Determines **optimal technical specifications** including **voltage levels (e.g. 330–400 kV)** and **conductor types** to minimize line losses over long distances while meeting load and reliability requirements.

**When to use:** After demand and route length are known; use to set voltage, conductor, and thermal capacity for the corridor.

**Key concepts:** Voltage level, conductor type, losses, thermal capacity, N-1 or reliability criteria.

---

### 4. `optimize_substation_placement`

**What it does:** Optimizes **substation locations** to serve anchor loads efficiently. It determines the minimal number of step-down points required to connect the maximum number of high-value customers along the corridor.

**When to use:** When anchor loads and route are defined; use to place substations and define offtake points.

**Key concepts:** Step-down substations, anchor load connection, minimal substation count vs coverage.

---

### 5. `generate_phasing_strategy`

**What it does:** Aligns **transmission development with highway construction and anchor load timelines**. It creates a **2–3 phase plan** so that power is available when industry and transport become operational.

**When to use:** To produce a phased rollout (e.g. Phase 1: trunk; Phase 2: extensions; Phase 3: last-mile) for planning and financing.

**Key concepts:** Phasing, construction sequence, demand ramp-up, readiness for anchor loads.

---

### 6. `generate_cost_estimates`

**What it does:** Generates **detailed CAPEX and OPEX estimates**. It uses regional unit costs for lines, substations, and labor to produce a project budget, typically with a contingency (e.g. 15%).

**When to use:** After routes, voltage, substations, and phasing are set; use to produce the cost base for financial modeling and financing optimization.

**Key concepts:** CAPEX (lines, substations, civils, contingency), OPEX (O&M, insurance), regional unit rates.

---

## Typical Workflow

1. **Routes:** Use `refine_optimized_routes` to turn Geospatial paths into engineering alignments within RoW.
2. **Colocation:** Use `quantify_colocation_benefits` to quantify savings from shared corridor.
3. **Sizing:** Use `size_voltage_and_capacity` to set voltage and conductor for the corridor.
4. **Substations:** Use `optimize_substation_placement` to place step-downs and connect anchor loads.
5. **Phasing:** Use `generate_phasing_strategy` to align build-out with highway and demand.
6. **Costs:** Use `generate_cost_estimates` to produce CAPEX/OPEX for the Financing and Economic Impact agents.
