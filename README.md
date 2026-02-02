# Corridor Intelligence Platform

A platform of AI agents built with LangGraph and LangChain for corridor planning: geospatial analysis, opportunity identification, infrastructure optimization, economic impact modeling, financing, stakeholder intelligence, and real-time monitoring. The agents work along a **critical path** from foundation (geospatial, opportunity) through optimization (infrastructure, economic, financing) to support (stakeholder, monitoring).

## Table of Contents

- [Overview](#overview)
- [Agents](#agents)
- [Critical Path](#critical-path)
- [Environment Setup](#environment-setup)
- [Running the Platform](#running-the-platform)
- [Project Structure](#project-structure)
- [Development](#development)

## Overview

The Corridor Intelligence Platform provides seven specialized agents that support end-to-end corridor planning (e.g. Abidjan–Lagos scale):

- **Tier 1 (Foundation):** Geospatial Intelligence, Opportunity Identification — provide the data all other agents depend on.
- **Tier 2 (Optimization):** Infrastructure Optimization, Economic Impact Modeling, Financing Optimization — can be developed in parallel once Tier 1 is in place.
- **Tier 3 (Support):** Stakeholder Intelligence, Real-time Monitoring — support implementation and engagement.



## Agents

| # | Agent | Purpose | Key Deliverables |
|---|--------|---------|------------------|
| **1** | **Geospatial Intelligence** | Analyze satellite imagery and geospatial data for infrastructure, routes, co-location, and constraints. | Infrastructure detections; 50–100 route variants with geospatial scoring; co-location analysis (15–25% CAPEX savings); terrain and environmental constraints. |
| **2** | **Opportunity Identification** | Scan corridor zones for economic opportunities and anchor loads. | Catalog of 45–57 anchor loads; demand profiles (current & projected MW); bankability scores; growth trajectories. |
| **3** | **Infrastructure Optimization** | Optimal transmission routes, voltage, phasing, and technical specs. | Top 5–10 routes; voltage (330–400 kV), capacity, phasing; co-location savings ($120–180M); CAPEX/OPEX estimates. |
| **4** | **Economic Impact Modeling** | Quantify GDP, jobs, poverty reduction, and sector catalytic effects. | GDP multiplier ($1.80–$2.20 per $1); job creation (200k–300k); poverty metrics; scenario comparison. |
| **5** | **Financing Optimization** | Model blended finance and DFI matching for target returns. | 20–30 financing scenarios; grants, concessional debt, commercial debt, equity; IRR/DSCR/NPV; DFI engagement plan. |
| **6** | **Stakeholder Intelligence** | Map stakeholders, influence networks, and engagement strategies. | 150–200 stakeholders; influence map; 4-phase engagement roadmap (24 months); risk register; sentiment monitoring. |
| **7** | **Real-time Monitoring** | Track implementation, performance, and early warnings. | Progress dashboard; budget vs. actual; anchor load realization; alerts; adaptive recommendations. |

Details on dependencies, outputs used by other agents, and milestones are in [PLAN.MD](./PLAN.MD).

## Critical Path

From [PLAN.MD](./PLAN.MD):

1. **Geospatial** → Foundation for everything.
2. **Opportunity** → Revenue and anchor loads.
3. **Infrastructure** → Technical design and costs.
4. **Economic** → Development impact.
5. **Financing** → Investment structure.
6. **Stakeholder** → Engagement strategy.
7. **Monitoring** → Implementation tracking.

**Dependency order:** #1 → #2 → (#3 + #4 + #5 in parallel) → (#6 + #7 in parallel).

**Milestones:**

- **Milestone 1:** Geospatial agent at 80% accuracy → enables Opportunity agent.
- **Milestone 2:** Opportunity agent delivers anchor load catalog → enables Infrastructure, Economic, Financing agents.
- **Milestone 3:** Core analytics complete → Abidjan–Lagos pilot feasibility; first DFI presentations; start Stakeholder and Monitoring.
- **Milestone 4:** Full platform operational → production-ready; scale to 5+ corridors.

## Environment Setup

### 1. Copy environment file

```bash
cp .env.example .env
```

### 2. Configure `.env`

Edit `.env` and set at least:

```env
OPENAI_API_KEY="your_openai_api_key_here"
# Optional:
GEMINI_API_KEY="your_gemini_api_key_here"
TAVILY_API_KEY="your_tavily_api_key_here"
LANGSMITH_TRACING=true
LANGSMITH_API_KEY="your_langsmith_api_key_here"
LANGSMITH_PROJECT="corridor_intelligence"
```

- **OpenAI** (required for default LLM): https://platform.openai.com/api-keys  
- **Gemini** (optional): https://makersuite.google.com/app/apikey  
- **Tavily** (optional, search): https://tavily.com/  
- **LangSmith** (optional, tracing): https://smith.langchain.com/

Do not commit `.env` or share API keys.

### 3. Install dependencies

From the project root, install the project and its dependencies.

**Option A — using [uv](https://docs.astral.sh/uv/) (recommended):**

```bash
uv sync
```

This creates a virtual environment (if needed) and installs dependencies from `pyproject.toml` and `uv.lock`.

**Option B — using pip:**

```bash
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
pip install -e .
```

This installs the project in editable mode with all dependencies from `pyproject.toml`.

Ensure you are using **Python 3.13** (see `.python-version` or `pyproject.toml`).

## Running the Platform

### Local development (Python 3.13)

From the project root:

```bash
langgraph dev
```

Then:

- **API:** http://127.0.0.1:2024  
- **Studio UI:** https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024  
- **API Docs:** http://127.0.0.1:2024/docs  



### Docker

```bash
docker compose up
```

- **Base URL:** http://localhost:8000  
- **API Docs:** http://localhost:8000/docs  

All seven agents are registered in `langgraph.json` and in the Dockerfile `LANGSERVE_GRAPHS` env.




## Development

- **Dependencies:** See [Environment Setup → Install dependencies](#3-install-dependencies) above.
- **Lint / format:** Use your preferred Python linter and formatter.  
- **Adding an agent:** Add a new folder under `src/agents/` with the same structure (context, middleware, prompts, state), register it in `langgraph.json` and in the Dockerfile `LANGSERVE_GRAPHS`.  
- **Planning and milestones:** See [PLAN.MD](./PLAN.MD) for agent order, dependencies, and deliverables.
