"""Suggestion generation and review endpoints."""
import json
from datetime import date
from fastapi import APIRouter, HTTPException, Query
from models import SuggestionResponse, SuggestionEdit
from db import execute, execute_one, execute_insert
from ai.agnes import generate_suggestions
from ai.mem9 import store_feedback, get_learned_preferences

router = APIRouter()


@router.get("/suggestions", response_model=list[SuggestionResponse])
async def list_suggestions(
    status: str | None = None,
    date: date | None = None,
):
    sql = "SELECT * FROM suggestions WHERE 1=1"
    params = []
    if status:
        sql += " AND status = %s"
        params.append(status)
    if date:
        sql += " AND date = %s"
        params.append(date)
    sql += " ORDER BY created_at DESC"
    rows = execute(sql, params)
    return [_row_to_suggestion(r) for r in rows]


@router.post("/suggestions/generate")
async def generate(
    date: date = Query(...),
    force: bool = Query(False),
):
    """Generate AI suggestions for a date using Agnes AI."""
    # Fetch raw events for the date
    raw_events = execute(
        "SELECT * FROM raw_events WHERE event_date = %s",
        (date,),
    )

    if not raw_events:
        return {"message": "No raw events for this date. Sync connectors first.", "count": 0}

    # Format raw events as text for the AI
    sections = {}
    for event in raw_events:
        connector = event["connector_id"]
        data = event["raw_data"]
        if isinstance(data, str):
            data = json.loads(data)
        if connector not in sections:
            sections[connector] = []
        sections[connector].append(json.dumps(data, indent=2, ensure_ascii=False))

    raw_text = ""
    for connector, items in sections.items():
        raw_text += f"\n### {connector}\n"
        raw_text += "\n---\n".join(items)

    # Build context: existing entries + suggestions
    existing_entries = execute(
        "SELECT category, description FROM entries WHERE date = %s AND deleted = 0",
        (date,),
    )
    existing_suggestions = execute(
        "SELECT suggested_category, suggested_description, status FROM suggestions WHERE date = %s",
        (date,),
    )

    context_parts = []
    if existing_entries:
        context_parts.append("Already logged entries:\n" + "\n".join(
            f"- [{e['category']}] {e['description']}" for e in existing_entries
        ))
    if existing_suggestions:
        context_parts.append("Existing suggestions:\n" + "\n".join(
            f"- [{s['status']}] [{s['suggested_category']}] {s['suggested_description']}"
            for s in existing_suggestions
        ))

    # Get learned preferences from Mem9
    preferences = await get_learned_preferences()
    if preferences:
        context_parts.append(f"Learned preferences:\n{preferences}")

    context = "\n\n".join(context_parts)

    # Call Agnes AI
    try:
        suggestions = await generate_suggestions(raw_text, context)
    except Exception as e:
        raise HTTPException(500, f"AI generation failed: {str(e)}")

    # Store suggestions
    count = 0
    for s in suggestions:
        execute_insert(
            """INSERT INTO suggestions
               (date, suggested_category, suggested_description, suggested_stakeholders,
                suggested_work_type, suggested_delegation_score, suggested_time_estimate,
                suggested_impact_level, suggested_scope_tag, suggested_scope_response,
                suggested_escalated_from, reasoning, confidence)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                date,
                s.get("category"),
                s.get("description"),
                json.dumps(s.get("stakeholders")) if s.get("stakeholders") else None,
                s.get("work_type"),
                s.get("delegation_score"),
                s.get("time_estimate"),
                s.get("impact_level"),
                s.get("scope_tag"),
                s.get("scope_response"),
                s.get("escalated_from"),
                s.get("reasoning"),
                s.get("confidence"),
            ),
        )
        count += 1

    # Mark raw events as processed
    execute(
        "UPDATE raw_events SET processed = 1 WHERE event_date = %s AND processed = 0",
        (date,),
    )

    return {"message": f"Generated {count} suggestions", "count": count}


@router.post("/suggestions/{suggestion_id}/accept")
async def accept_suggestion(suggestion_id: int):
    """Accept a suggestion and create an entry from it."""
    row = execute_one("SELECT * FROM suggestions WHERE id = %s", (suggestion_id,))
    if not row:
        raise HTTPException(404, "Suggestion not found")

    stakeholders = row.get("suggested_stakeholders")
    if isinstance(stakeholders, str):
        stakeholders = json.loads(stakeholders) if stakeholders else None

    entry_id = execute_insert(
        """INSERT INTO entries
           (date, category, description, stakeholders, work_type,
            delegation_score, time_estimate, impact_level, scope_tag,
            scope_response, escalated_from, reasoning, source, suggestion_id)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'suggestion', %s)""",
        (
            row["date"],
            row["suggested_category"],
            row["suggested_description"],
            json.dumps(stakeholders) if stakeholders else None,
            row.get("suggested_work_type"),
            row.get("suggested_delegation_score"),
            row.get("suggested_time_estimate"),
            row.get("suggested_impact_level"),
            row.get("suggested_scope_tag"),
            row.get("suggested_scope_response"),
            row.get("suggested_escalated_from"),
            row.get("reasoning"),
            suggestion_id,
        ),
    )

    execute(
        "UPDATE suggestions SET status = 'accepted', resolved_entry_id = %s WHERE id = %s",
        (entry_id, suggestion_id),
    )

    await store_feedback(suggestion_id, "accepted")
    return {"ok": True, "entry_id": entry_id}


@router.post("/suggestions/{suggestion_id}/edit")
async def edit_and_accept(suggestion_id: int, edit: SuggestionEdit):
    """Edit a suggestion and accept it as an entry."""
    row = execute_one("SELECT * FROM suggestions WHERE id = %s", (suggestion_id,))
    if not row:
        raise HTTPException(404, "Suggestion not found")

    # Merge edits with suggestion defaults
    category = edit.category or row["suggested_category"]
    description = edit.description or row["suggested_description"]
    stakeholders = edit.stakeholders
    if stakeholders is None:
        stakeholders = row.get("suggested_stakeholders")
        if isinstance(stakeholders, str):
            stakeholders = json.loads(stakeholders) if stakeholders else None

    entry_id = execute_insert(
        """INSERT INTO entries
           (date, category, description, stakeholders, work_type,
            delegation_score, time_estimate, impact_level, scope_tag,
            scope_response, escalated_from, reasoning, source, suggestion_id)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'suggestion', %s)""",
        (
            row["date"], category, description,
            json.dumps(stakeholders) if stakeholders else None,
            edit.work_type or row.get("suggested_work_type"),
            edit.delegation_score or row.get("suggested_delegation_score"),
            edit.time_estimate or row.get("suggested_time_estimate"),
            edit.impact_level or row.get("suggested_impact_level"),
            edit.scope_tag or row.get("suggested_scope_tag"),
            edit.scope_response or row.get("suggested_scope_response"),
            edit.escalated_from or row.get("suggested_escalated_from"),
            row.get("reasoning"),
            suggestion_id,
        ),
    )

    execute(
        "UPDATE suggestions SET status = 'edited', resolved_entry_id = %s WHERE id = %s",
        (entry_id, suggestion_id),
    )

    await store_feedback(suggestion_id, "edited", edit.model_dump(exclude_unset=True))
    return {"ok": True, "entry_id": entry_id}


@router.post("/suggestions/{suggestion_id}/dismiss")
async def dismiss_suggestion(suggestion_id: int):
    execute(
        "UPDATE suggestions SET status = 'dismissed' WHERE id = %s",
        (suggestion_id,),
    )
    await store_feedback(suggestion_id, "dismissed")
    return {"ok": True}


@router.post("/suggestions/{suggestion_id}/restore")
async def restore_suggestion(suggestion_id: int):
    execute(
        "UPDATE suggestions SET status = 'pending' WHERE id = %s AND status = 'dismissed'",
        (suggestion_id,),
    )
    return {"ok": True}


def _row_to_suggestion(row: dict) -> SuggestionResponse:
    stakeholders = row.get("suggested_stakeholders")
    if isinstance(stakeholders, str):
        stakeholders = json.loads(stakeholders)
    return SuggestionResponse(
        id=row["id"],
        date=row["date"],
        status=row["status"],
        suggested_category=row.get("suggested_category"),
        suggested_description=row.get("suggested_description"),
        suggested_stakeholders=stakeholders,
        suggested_work_type=row.get("suggested_work_type"),
        suggested_delegation_score=row.get("suggested_delegation_score"),
        suggested_time_estimate=row.get("suggested_time_estimate"),
        suggested_impact_level=row.get("suggested_impact_level"),
        suggested_notes=row.get("suggested_notes"),
        suggested_scope_tag=row.get("suggested_scope_tag"),
        suggested_scope_response=row.get("suggested_scope_response"),
        suggested_escalated_from=row.get("suggested_escalated_from"),
        reasoning=row.get("reasoning"),
        confidence=row.get("confidence"),
        source_connector=row.get("source_connector"),
        created_at=row.get("created_at"),
    )
