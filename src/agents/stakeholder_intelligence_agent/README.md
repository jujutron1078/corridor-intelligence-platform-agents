# Stakeholder Intelligence Agent

This agent maps and analyzes the stakeholder landscape for the corridor. It identifies and catalogs stakeholders (governments, DFIs, utilities, private sector, civil society), analyzes influence networks, generates engagement roadmaps, assesses stakeholder risks, produces tailored messaging, and tracks engagement sentiment over time.

---

## Shared Tools (Platform-Wide)

All agents use these common tools:

| Tool | Purpose |
|------|--------|
| **think_tool** | Step-by-step reasoning and documentation of assumptions. |
| **write_todos** | Structured task list for multi-step workflows. |

---

## Domain Tools

### 1. `map_stakeholder_ecosystem`

**What it does:** Identifies **150–200 stakeholders** across governments, DFIs, utilities, private sector, and civil society. It uses official registries and news to build a comprehensive database of entities that are impacted by or impact the corridor.

**When to use:** At the start of stakeholder work to establish the full set of actors to engage.

**Key concepts:** Stakeholder categories (government, DFI, utility, private, civil society), coverage and representativeness.

---

### 2. `analyze_influence_networks`

**What it does:** Maps **relationships, decision-making power, and influence pathways**. It uses graph analysis to identify **"Gatekeepers"**, **"Champions"**, and **"Influencers"** within the corridor’s political and financial ecosystem.

**When to use:** After mapping the ecosystem; use to decide who can unblock decisions, who to nurture as champions, and who influences whom.

**Key concepts:** Influence graph, gatekeepers (control access), champions (support), influencers (shape opinion).

---

### 3. `generate_engagement_roadmap`

**What it does:** Recommends **sequencing and tactics for stakeholder outreach**. It phases engagement from core champions (e.g. Months 1–4) through to final regulatory approvals (e.g. Months 19–24).

**When to use:** To produce a time-bound engagement plan aligned with project milestones and approvals.

**Key concepts:** Phased engagement, champions first, regulatory and political sequencing.

---

### 4. `assess_stakeholder_risks`

**What it does:** Identifies **potential opposition, conflicts of interest, and political sensitivities**. It flags stakeholders who may oppose the project due to environmental concerns, competing interests, or other reasons.

**When to use:** To anticipate resistance and plan mitigation or dialogue.

**Key concepts:** Opposition risk, conflict of interest, political sensitivity, environmental/social concerns.

---

### 5. `generate_tailored_messaging`

**What it does:** **Tailors communication messages by stakeholder type and interests**. It ensures that a DFI receives "Development Impact" data while a mining CEO receives "Reliability and OPEX" data, and adapts tone and content accordingly.

**When to use:** When preparing briefs, presentations, or outreach materials for different audiences.

**Key concepts:** Message tailoring, audience (DFI vs utility vs private sector), key messages per segment.

---

### 6. `track_engagement_sentiment`

**What it does:** Tracks **stakeholder sentiment and engagement progress**. It uses NLP on news, social media, and meeting transcripts to provide a real-time view of project support vs. opposition.

**When to use:** Continuously or periodically, to monitor whether sentiment is improving or deteriorating and to adjust engagement tactics.

**Key concepts:** Sentiment (support/neutral/opposition), sources (news, social, meetings), trend over time.

---

## Typical Workflow

1. **Mapping:** Use `map_stakeholder_ecosystem` to build the full list of 150–200 stakeholders.
2. **Influence:** Use `analyze_influence_networks` to identify gatekeepers, champions, and influencers.
3. **Plan:** Use `generate_engagement_roadmap` to sequence outreach and tie it to project phases.
4. **Risks:** Use `assess_stakeholder_risks` to flag opposition and conflicts.
5. **Messaging:** Use `generate_tailored_messaging` to prepare audience-specific communications.
6. **Tracking:** Use `track_engagement_sentiment` to monitor support/opposition and refine tactics.

This agent supports permitting, partnership building, and risk mitigation throughout the corridor lifecycle.
