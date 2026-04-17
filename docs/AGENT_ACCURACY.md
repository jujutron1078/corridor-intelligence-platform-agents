# Agent Accuracy Playbook

The orchestrator was returning generic answers and the map wasn't rendering overlays. This doc explains **why** and exactly what to change when you have LLM credits to test against.

## 1. Turn on LangSmith tracing FIRST

Without traces you're debugging blind. One env var, zero code changes:

```bash
# .env
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_pt_...
LANGSMITH_PROJECT=corridor_intelligence
```

Every agent run will show up at https://smith.langchain.com. You can inspect which tool the LLM picked, what payload it sent, what came back, and where synthesis dropped the ball.

## 2. The four most likely causes of generic answers

Ordered by probability based on a code read of `src/api/services/chat_service.py` and the tool return shapes:

### a) The LLM is answering from general knowledge instead of calling a tool

**Symptom**: no tool calls in the LangSmith trace, just a direct response.

**Fix**: the orchestrator prompt (`src/agents/orchestrator_agent/prompts/prompt.py:6-141`) already says "NEVER give generic answers when you can query actual data", but LLMs bend this easily. Add a hard rule at the top:

```
## HARD RULE
If the user's message mentions ANY of: investment, opportunity, trade, energy,
power plant, road, port, conflict, flood, terrain, route, infrastructure,
agriculture, tourism, stakeholder, financing, GDP, jobs, a country name, a city
name — you MUST call a tool before responding. Never answer such questions from
training data. If you cannot decide which tool, call think_tool first.
```

### b) The tool is called but its output doesn't match the UI overlay schema

**Symptom**: tool ran, agent answered with real numbers, but map stayed empty.

The UI parses tool outputs in `corridor_agent_ui/lib/map-overlay.ts:1913 extractMapOverlayData()`. It looks for specific keys — if the payload shape drifts, nothing renders.

**Map overlay schema the UI expects** (from `lib/map-overlay.ts:21-38`):

| Tool result key | UI overlay field | Shape |
|---|---|---|
| `geocode_location` → `resolved_locations[*]` | `points[]` | `{name, latitude, longitude, confidence}` |
| `define_corridor` → `aoi_polygon` | `polygon` | GeoJSON Polygon |
| `terrain_analysis` → `segment_analysis[*]` | `terrainAnalysis.segmentAnalysis[]` | `{segment_id, start_km, end_km, start_coordinate, end_coordinate, avg_slope, flood_risk}` |
| `environmental_constraints` → `protected_area_conflicts`, `wetland_and_water_body_conflicts`, `human_safety_conflicts` | `noGoZones[]` | Each item has `{zone_id, name, coordinates: {latitude, longitude}}` |
| `infrastructure_detection` → `infrastructure_identified` | `infrastructureDetections[]` | `{asset_type, coordinates, risk_severity}` |
| `route_optimization` / `refine_optimized_routes` → `route_variants[*]` | `routeVariants[]` | `{variant_id, geometry: GeoJSON LineString}` |
| `scan_anchor_loads` → anchor catalog | `points[]` with sector tag | — |
| `economic_gap_analysis` → gaps | `economicGaps[]` | `{gap_id, latitude, longitude, severity, investment_priority}` |
| `prioritize_opportunities` → ranked list | `prioritizedOpportunities[]` | `{rank, bankability_score, latitude, longitude, phase, year5_mw}` |

**Audit checklist**: for each tool, run it once, dump the JSON, grep for the required keys. Anywhere the parser falls back to undefined, the overlay breaks silently.

The new `climate_risk_tool` (added in this session) was written to match the `ClimateRiskSummary` type in `lib/map-overlay.ts:173-178` — verify terrain tool outputs fold its fields (`drought_risk`, `heat_risk`, `coastal_flood_risk`) into the segments before committing to that wiring.

### c) The orchestrator rewrites agent output (especially from opportunity_identification_agent)

**Symptom**: opportunity cards fail to render — the frontend depends on ```opportunity-json``` code blocks inside the agent's message text.

The orchestrator prompt already warns about this at lines 102-114 of `prompt.py`. If you see this happening, it usually means a middleware (`trim_tool_messages`, `inject_context`) stripped the code block. Check LangSmith for the final `messages[]` sent to the model.

### d) Mock fallbacks leaking through

`terrain_analysis_tool/tool.py:16-101` has `CORRIDOR_SEGMENTS` — this is NOT a mock; it's expert-compiled reference data enriched with live GEE reads where available. Leave it. But if you see generic/wrong flood classifications, that's usually because `pipeline_bridge.get_flood_risk_data()` failed silently (`tool.py:155-168` logs a warning and skips). Check logs for `"Flood risk data unavailable"`.

## 3. The tool-description hygiene checklist

Every tool's `description.py` should contain, in this order:

1. **One-sentence purpose** — what it does.
2. **WHEN TO USE** — 3-5 bullet examples of prompts that should trigger it.
3. **Input example** — a full valid JSON call.
4. **Output example** — truncated JSON showing the shape the UI needs.
5. **Anti-examples** (optional) — when NOT to use it.

Audit status (based on a spot-check):

| Tool | WHEN TO USE? | Input example? | Output shape? |
|---|---|---|---|
| geocode_location_tool | ✅ | ✅ | ✅ |
| terrain_analysis_tool | ⚠️ short | ❌ | ❌ |
| environmental_constraints_tool | ? | ? | ? |
| infrastructure_detection_tool | ? | ? | ? |
| route_optimization_tool | ? | ? | ? |
| climate_risk_tool | ✅ | ✅ | ✅ |

The rest need beefed docstrings. Order of effort-vs-impact: terrain + environmental first (they produce the most map layers).

## 4. Quick diagnostic script

```bash
# With .env configured and venv active
python -c "
from src.agents.orchestrator_agent.agent import agent
import asyncio

async def probe(msg):
    async for event in agent.astream({'messages':[('user', msg)]}, config={'configurable':{'thread_id':'probe'}}):
        for node, update in event.items():
            if 'messages' in update:
                for m in update['messages']:
                    print(node, '→', m.__class__.__name__, str(m.content)[:200])

asyncio.run(probe('Show me agriculture investment opportunities in Ghana'))
"
```

This prints the tool-call chain. If you see only AIMessage (no ToolMessage), the orchestrator skipped delegation — fix with the HARD RULE in §2a.

## 5. Prompt-tightening diffs (do these, in this order)

1. Add the HARD RULE at the top of `orchestrator_agent/prompts/prompt.py`.
2. For each geospatial tool, extend `description.py` with an Output example showing the overlay-parsable shape.
3. Add one line to every spatial tool's system prompt: *"Return field names exactly as shown. The frontend parser is case- and underscore-sensitive."*
4. Set `LANGSMITH_TRACING=true` in both dev and prod `.env`.

Ship those four — it'll close 80% of the accuracy gap without touching tool code.
