# Impact Tracker — Product Overview

> AI-powered managerial impact tracking that makes invisible work visible.

---

## 1. Problem Statement

### The Invisible Work Problem

Managers operate in a world of **invisible work**. Unlike engineers who ship code or designers who produce mockups, a manager's most valuable contributions — decisions made, blockers removed, alignment achieved — leave no tangible artifact.

**Pain points:**

- **"What did I actually do today?"** — At the end of a busy day filled with meetings, Slack threads, and 1:1s, managers struggle to articulate their impact
- **Evaluation gap** — Performance reviews require concrete examples, but most managerial impact is ephemeral and forgotten within days
- **Manual logging fails** — Daily journals and impact logs are abandoned within weeks because the cognitive overhead is too high
- **Scope creep is invisible** — Managers absorb cross-functional work without realizing how much of their time goes to tasks outside their core role
- **No feedback loop** — Without structured data, managers can't identify patterns in how they spend their time or whether they're focusing on high-impact activities

### Who experiences this?

Engineering managers, product managers, team leads — anyone whose job is to **multiply the output of others** rather than produce individual output.

---

## 2. Solution

### Impact Tracker: From Raw Activity to Structured Impact

Impact Tracker connects to the tools managers already use (calendar, Slack, code review platforms) and uses AI to **automatically detect and categorize impact items** from raw activity data.

**Core loop:**

```
Raw Activity Data → AI Analysis → Suggested Impact Items → Human Review → Structured Impact Log
```

The manager's only job is to **review and approve** — the AI does the heavy lifting of identifying what matters.

### 7 Impact Categories

Every managerial action is classified into one of 7 research-backed categories:

| Category | Description | Example |
|----------|-------------|---------|
| **DECISION** | Decisions made or influenced | "Decided to postpone migration to Q3 based on risk assessment" |
| **BLOCKER_REMOVED** | Unblocking others | "Resolved CI pipeline issue blocking 3 engineers" |
| **ALIGNMENT** | Syncs, 1:1s, stakeholder alignment | "Aligned product and engineering on Q2 roadmap priorities" |
| **STRUCTURE** | Processes, frameworks, documentation | "Introduced RFC process for architecture decisions" |
| **TEAM_DEV** | Coaching, hiring, team development | "Conducted growth conversation with junior engineer about tech lead path" |
| **STRATEGIC_ANTICIPATION** | Proactive risk/opportunity identification | "Identified vendor lock-in risk and initiated alternative evaluation" |
| **FIRES_HANDLED** | Urgent issues resolved | "Coordinated incident response for production outage" |

---

## 3. User Behavior Flow

### Daily Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                        DAILY WORKFLOW                           │
│                                                                 │
│  ① Sync         ② Generate        ③ Review         ④ Log       │
│  ┌─────────┐    ┌──────────┐    ┌────────────┐   ┌─────────┐  │
│  │Connectors│───▶│AI Suggests│───▶│Accept/Edit/│──▶│ Impact  │  │
│  │  Pull    │    │  Items   │    │  Dismiss   │   │  Items  │  │
│  └─────────┘    └──────────┘    └────────────┘   └─────────┘  │
│                                                       │         │
│  ⑤ Day Summary                                       ▼         │
│  ┌──────────────────────┐                      ┌─────────┐     │
│  │ Cognitive Load: L/M/H│                      │ Growth  │     │
│  │ Energy: Strategic/    │                      │Dashboard│     │
│  │         Mixed/Reactive│                      └─────────┘     │
│  └──────────────────────┘                                       │
└─────────────────────────────────────────────────────────────────┘
```

### Step-by-step

1. **Sync connectors** — Pull raw data from calendar, Slack, web search (Bright Data)
2. **Generate suggestions** — AI (Agnes AI) analyzes raw events and proposes impact items with reasoning
3. **Review** — Manager accepts, edits, or dismisses each suggestion. Feedback is stored in Mem9 for learning
4. **Log accumulates** — Structured impact items build up over days/weeks
5. **Day summary** — Optionally record cognitive load (L/M/H) and energy mode (Strategic/Mixed/Reactive)

### Learning Loop

```
User accepts suggestion → Mem9 stores preference
User edits suggestion  → Mem9 learns correction
User dismisses         → Mem9 learns what to avoid
                              ↓
              Next generation is more accurate
```

---

## 4. Key Features

### AI-Powered Suggestion Generation
- Agnes AI (via ZenMux, OpenAI-compatible) analyzes raw activity data
- Generates structured suggestions with reasoning, confidence score, and evidence
- Respects existing entries to avoid duplicates

### Multi-Source Data Ingestion
- **Bright Data SERP** — Enriches context by searching topics found in activity data
- **Planned connectors:** Slack, Google Calendar, Fathom (meeting transcription), Claude Code sessions

### Persistent Learning (Mem9)
- Every accept/edit/dismiss action is stored as feedback
- Learned preferences are injected into future AI prompts
- The system gets smarter with use — adapting to each manager's definition of "impact"

### Scope Tracking
- Tags each item: Core Role, Adjacent Ops, Cross-Functional, BAU Overhead, Strategic Initiative
- When work is out-of-scope, records the response: Advisory, Tradeoff, No, Absorbed
- Makes scope creep visible over time

### Delegation Scoring
- 1-5 scale per item: could this have been delegated?
- Over time, reveals patterns of under-delegation

---

## 5. Technology Architecture

```
┌─────────────────────────────────────────────────┐
│                   Frontend                       │
│            HTML + CSS + Vanilla JS               │
│         (Single Page, Tab Navigation)            │
└────────────────────┬────────────────────────────┘
                     │ REST API
┌────────────────────▼────────────────────────────┐
│              FastAPI (Python)                     │
│                                                  │
│  ┌──────────┐ ┌────────────┐ ┌──────────────┐  │
│  │ Entries   │ │ Suggestions│ │ Connectors   │  │
│  │ Router    │ │ Router     │ │ Router       │  │
│  └──────────┘ └──────┬─────┘ └──────┬───────┘  │
│                      │              │            │
│              ┌───────▼───────┐  ┌───▼────────┐  │
│              │ Agnes AI      │  │ Bright Data│  │
│              │ (ZenMux API)  │  │ SERP API   │  │
│              └───────────────┘  └────────────┘  │
│                      │                           │
│              ┌───────▼───────┐                   │
│              │    Mem9       │                   │
│              │ (Persistent   │                   │
│              │  Memory)      │                   │
│              └───────────────┘                   │
└────────────────────┬────────────────────────────┘
                     │ MySQL Protocol (SSL)
┌────────────────────▼────────────────────────────┐
│           TiDB Cloud Zero                        │
│     (MySQL-compatible, serverless)                │
│                                                  │
│  Tables: entries, suggestions, raw_events,       │
│          daily_meta, connector_config, drafts     │
└──────────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│              Zeabur (Deploy)                     │
└──────────────────────────────────────────────────┘
```

### Code Structure

```
Hackathon/
├── main.py              # FastAPI app entry point
├── config.py            # Pydantic settings (env vars)
├── db.py                # TiDB connection + schema init
├── models.py            # Request/response models
├── ai/
│   ├── agnes.py         # Agnes AI suggestion generation
│   └── mem9.py          # Mem9 persistent memory client
├── connectors/
│   └── bright_data.py   # Bright Data SERP connector
├── routers/
│   ├── entries.py       # Impact item CRUD
│   ├── suggestions.py   # AI suggestion lifecycle
│   ├── daily_meta.py    # Day-level metadata
│   └── connectors.py    # Connector sync endpoints
└── static/
    ├── index.html       # Single-page UI
    ├── style.css        # Dark theme styles
    └── app.js           # Frontend logic
```

---

## 6. Sponsor Technology Usage

| Sponsor | Role in Product | Integration Point |
|---------|----------------|-------------------|
| **Zeabur** | Deployment & hosting | `npx zeabur deploy` — production hosting |
| **TiDB Cloud Zero** | Primary database | MySQL-compatible serverless DB for all data storage (6 tables) |
| **Agnes AI (ZenMux)** | Core AI engine | OpenAI-compatible API for analyzing raw activity → impact suggestions |
| **Bright Data** | Data enrichment | SERP API enriches context by searching topics from manager's activity |
| **Mem9** | Learning memory | Stores user feedback (accept/edit/dismiss) to improve future suggestions |

---

## 7. Future Vision

### Short-term (Post-hackathon)
- **Growth Dashboard** — Weekly/monthly trend visualization of impact categories, scope distribution, delegation patterns
- **More connectors** — Slack (messages/reactions), Google Calendar (meeting context), Fathom (meeting transcripts)
- **Archive view** — Historical browse and search across all impact items

### Medium-term
- **Weekly digest** — AI-generated summary: "This week you made 12 decisions, removed 5 blockers, and spent 30% of time on cross-functional work"
- **Pattern detection** — "You're spending more time on FIRES_HANDLED this month — is something structurally broken?"
- **Export** — Generate performance review talking points from accumulated data

### Long-term
- **Team edition** — Multiple managers sharing anonymized patterns and benchmarks
- **Manager coaching** — AI-powered coaching based on impact patterns ("You haven't logged any TEAM_DEV items in 2 weeks — consider scheduling growth conversations")
- **Organization insights** — Aggregate view of where managerial energy goes across an organization
