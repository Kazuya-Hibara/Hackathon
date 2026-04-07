# Architecture

## Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | HTML + CSS + Vanilla JS | Single-page app with tab navigation |
| **Backend** | FastAPI (Python) | REST API server |
| **Database** | TiDB Cloud Zero | MySQL-compatible serverless DB |
| **AI** | Agnes AI via ZenMux | Impact suggestion generation (OpenAI-compatible API) |
| **Search** | Bright Data SERP API | Web search for context enrichment |
| **Memory** | Mem9 (mnemo-server) | Persistent learning from user feedback |
| **Deploy** | Zeabur | Cloud hosting |

## Data Flow

```
Connectors (Bright Data, future: Slack/GCal/Fathom)
        │
        ▼
   raw_events table ──▶ Agnes AI analyzes ──▶ suggestions table
                                                    │
                                          User: Accept/Edit/Dismiss
                                                    │
                                                    ▼
                                             entries table
                                                    │
                                          Feedback → Mem9
                                          (learning loop)
```

## Database Schema

6 tables in TiDB Cloud Zero:

- **entries** — Impact items logged per day (manual + accepted suggestions)
- **suggestions** — AI-generated proposals (pending → accepted/edited/dismissed)
- **raw_events** — Ingested data from connectors (processed flag for dedup)
- **daily_meta** — Day-level context (cognitive load, energy mode)
- **connector_config** — Sync status per connector
- **drafts** — Form auto-save

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/entries` | List entries (filter by date, deleted) |
| POST | `/api/entries` | Create entry |
| PUT | `/api/entries/{id}` | Update entry |
| DELETE | `/api/entries/{id}` | Soft delete |
| POST | `/api/suggestions/generate` | Generate AI suggestions for a date |
| POST | `/api/suggestions/{id}/accept` | Accept suggestion → create entry |
| POST | `/api/suggestions/{id}/edit` | Edit + accept suggestion |
| POST | `/api/suggestions/{id}/dismiss` | Dismiss suggestion |
| GET/PUT | `/api/daily-meta/{date}` | Day summary (cognitive load, energy) |
| GET | `/api/connectors` | List connector statuses |
| POST | `/api/connectors/{id}/sync` | Trigger connector sync |
| GET | `/health` | Health check |
