"""Connector sync endpoints."""
from datetime import date
from fastapi import APIRouter, HTTPException
from models import ConnectorStatus, SyncRequest
from db import execute, execute_one
from connectors.bright_data import sync_bright_data

router = APIRouter()

AVAILABLE_CONNECTORS = ["bright_data", "claude_code", "claude_cowork", "slack", "gcal", "fathom"]


@router.get("/connectors", response_model=list[ConnectorStatus])
async def list_connectors():
    rows = execute("SELECT * FROM connector_config")
    existing = {r["connector_id"] for r in rows}
    result = []
    for cid in AVAILABLE_CONNECTORS:
        if cid in existing:
            row = next(r for r in rows if r["connector_id"] == cid)
            result.append(ConnectorStatus(**row))
        else:
            result.append(ConnectorStatus(connector_id=cid, enabled=False))
    return result


@router.post("/connectors/{connector_id}/sync")
async def sync_connector(connector_id: str, req: SyncRequest | None = None):
    if connector_id not in AVAILABLE_CONNECTORS:
        raise HTTPException(404, f"Unknown connector: {connector_id}")

    date_from = req.date_from if req else None
    date_to = req.date_to if req else None

    if connector_id == "bright_data":
        count = await sync_bright_data(date_from, date_to)
    else:
        raise HTTPException(501, f"Connector {connector_id} not yet implemented")

    # Update last_sync
    execute(
        """INSERT INTO connector_config (connector_id, enabled, last_sync)
           VALUES (%s, 1, NOW())
           ON DUPLICATE KEY UPDATE last_sync = NOW()""",
        (connector_id,),
    )

    return {"connector": connector_id, "events_synced": count}
