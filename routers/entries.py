"""Entry CRUD endpoints."""
import json
from datetime import date, datetime
from fastapi import APIRouter, Query, HTTPException
from models import EntryCreate, EntryUpdate, EntryResponse
from db import execute, execute_one, execute_insert, _is_sqlite

router = APIRouter()


@router.get("/entries", response_model=list[EntryResponse])
async def list_entries(
    date: date | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    include_deleted: bool = False,
):
    sql = "SELECT * FROM entries WHERE 1=1"
    params = []

    if not include_deleted:
        sql += " AND deleted = 0"
    if date:
        sql += " AND date = %s"
        params.append(date)
    if date_from:
        sql += " AND date >= %s"
        params.append(date_from)
    if date_to:
        sql += " AND date <= %s"
        params.append(date_to)

    sql += " ORDER BY created_at DESC"
    rows = execute(sql, params)
    return [_row_to_entry(r) for r in rows]


@router.post("/entries", response_model=EntryResponse)
async def create_entry(entry: EntryCreate):
    entry_id = execute_insert(
        """INSERT INTO entries (date, category, description, stakeholders,
           work_type, delegation_score, time_estimate, impact_level,
           notes, scope_tag, scope_response, escalated_from)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (
            entry.date, entry.category, entry.description,
            json.dumps(entry.stakeholders) if entry.stakeholders else None,
            entry.work_type, entry.delegation_score, entry.time_estimate,
            entry.impact_level, entry.notes, entry.scope_tag,
            entry.scope_response, entry.escalated_from,
        ),
    )
    row = execute_one("SELECT * FROM entries WHERE id = %s", (entry_id,))
    return _row_to_entry(row)


@router.put("/entries/{entry_id}", response_model=EntryResponse)
async def update_entry(entry_id: int, update: EntryUpdate):
    fields = []
    params = []
    for field, value in update.model_dump(exclude_unset=True).items():
        if field == "stakeholders" and value is not None:
            value = json.dumps(value)
        fields.append(f"{field} = %s")
        params.append(value)

    if not fields:
        raise HTTPException(400, "No fields to update")

    params.append(entry_id)
    execute(f"UPDATE entries SET {', '.join(fields)} WHERE id = %s", params)
    row = execute_one("SELECT * FROM entries WHERE id = %s", (entry_id,))
    if not row:
        raise HTTPException(404, "Entry not found")
    return _row_to_entry(row)


@router.delete("/entries/{entry_id}")
async def soft_delete_entry(entry_id: int):
    now_fn = "datetime('now')" if _is_sqlite() else "NOW()"
    execute(
        f"UPDATE entries SET deleted = 1, deleted_at = {now_fn} WHERE id = %s",
        (entry_id,),
    )
    return {"ok": True}


@router.post("/entries/{entry_id}/restore")
async def restore_entry(entry_id: int):
    execute(
        "UPDATE entries SET deleted = 0, deleted_at = NULL WHERE id = %s",
        (entry_id,),
    )
    return {"ok": True}


@router.delete("/entries/{entry_id}/permanent")
async def permanent_delete_entry(entry_id: int):
    execute("DELETE FROM entries WHERE id = %s AND deleted = 1", (entry_id,))
    return {"ok": True}


def _row_to_entry(row: dict) -> EntryResponse:
    stakeholders = row.get("stakeholders")
    if isinstance(stakeholders, str):
        stakeholders = json.loads(stakeholders)
    return EntryResponse(
        id=row["id"],
        date=row["date"],
        category=row["category"],
        description=row["description"],
        stakeholders=stakeholders,
        work_type=row.get("work_type"),
        delegation_score=row.get("delegation_score"),
        time_estimate=row.get("time_estimate"),
        impact_level=row.get("impact_level"),
        notes=row.get("notes"),
        scope_tag=row.get("scope_tag"),
        scope_response=row.get("scope_response"),
        escalated_from=row.get("escalated_from"),
        reasoning=row.get("reasoning"),
        source=row.get("source", "manual"),
        suggestion_id=row.get("suggestion_id"),
        deleted=bool(row.get("deleted", 0)),
        created_at=row.get("created_at"),
    )
