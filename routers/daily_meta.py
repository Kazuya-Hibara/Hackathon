"""Daily metadata endpoints."""
from datetime import date
from fastapi import APIRouter
from models import DailyMetaUpsert, DailyMetaResponse
from db import execute, execute_one

router = APIRouter()


@router.get("/daily-meta/{date}", response_model=DailyMetaResponse)
async def get_daily_meta(date: date):
    row = execute_one("SELECT * FROM daily_meta WHERE date = %s", (date,))
    if not row:
        return DailyMetaResponse(date=date)
    return DailyMetaResponse(**row)


@router.put("/daily-meta/{date}", response_model=DailyMetaResponse)
async def upsert_daily_meta(date: date, meta: DailyMetaUpsert):
    execute(
        """INSERT INTO daily_meta (date, cognitive_load, energy, summary)
           VALUES (%s, %s, %s, %s)
           ON DUPLICATE KEY UPDATE
           cognitive_load = VALUES(cognitive_load),
           energy = VALUES(energy),
           summary = VALUES(summary)""",
        (date, meta.cognitive_load, meta.energy, meta.summary),
    )
    row = execute_one("SELECT * FROM daily_meta WHERE date = %s", (date,))
    return DailyMetaResponse(**row)
