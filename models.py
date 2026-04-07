"""Pydantic models for request/response validation."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime


# --- Entries ---

class EntryCreate(BaseModel):
    date: date
    category: str
    description: str
    stakeholders: Optional[list[str]] = None
    work_type: Optional[str] = None
    delegation_score: Optional[int] = None
    time_estimate: Optional[str] = None
    impact_level: Optional[str] = None
    notes: Optional[str] = None
    scope_tag: Optional[str] = None
    scope_response: Optional[str] = None
    escalated_from: Optional[str] = None


class EntryUpdate(BaseModel):
    category: Optional[str] = None
    description: Optional[str] = None
    stakeholders: Optional[list[str]] = None
    work_type: Optional[str] = None
    delegation_score: Optional[int] = None
    time_estimate: Optional[str] = None
    impact_level: Optional[str] = None
    notes: Optional[str] = None
    scope_tag: Optional[str] = None
    scope_response: Optional[str] = None
    escalated_from: Optional[str] = None


class EntryResponse(BaseModel):
    id: int
    date: date
    category: str
    description: str
    stakeholders: Optional[list[str]] = None
    work_type: Optional[str] = None
    delegation_score: Optional[int] = None
    time_estimate: Optional[str] = None
    impact_level: Optional[str] = None
    notes: Optional[str] = None
    scope_tag: Optional[str] = None
    scope_response: Optional[str] = None
    escalated_from: Optional[str] = None
    reasoning: Optional[str] = None
    source: str = "manual"
    suggestion_id: Optional[int] = None
    deleted: bool = False
    created_at: Optional[datetime] = None


# --- Daily Meta ---

class DailyMetaUpsert(BaseModel):
    cognitive_load: Optional[str] = None  # L, M, H
    energy: Optional[str] = None  # STRATEGIC, MIXED, REACTIVE
    summary: Optional[str] = None


class DailyMetaResponse(BaseModel):
    date: date
    cognitive_load: Optional[str] = None
    energy: Optional[str] = None
    summary: Optional[str] = None


# --- Suggestions ---

class SuggestionResponse(BaseModel):
    id: int
    date: date
    status: str
    suggested_category: Optional[str] = None
    suggested_description: Optional[str] = None
    suggested_stakeholders: Optional[list[str]] = None
    suggested_work_type: Optional[str] = None
    suggested_delegation_score: Optional[int] = None
    suggested_time_estimate: Optional[str] = None
    suggested_impact_level: Optional[str] = None
    suggested_notes: Optional[str] = None
    suggested_scope_tag: Optional[str] = None
    suggested_scope_response: Optional[str] = None
    suggested_escalated_from: Optional[str] = None
    reasoning: Optional[str] = None
    confidence: Optional[float] = None
    source_connector: Optional[str] = None
    created_at: Optional[datetime] = None


class SuggestionEdit(BaseModel):
    category: Optional[str] = None
    description: Optional[str] = None
    stakeholders: Optional[list[str]] = None
    work_type: Optional[str] = None
    delegation_score: Optional[int] = None
    time_estimate: Optional[str] = None
    impact_level: Optional[str] = None
    notes: Optional[str] = None
    scope_tag: Optional[str] = None
    scope_response: Optional[str] = None
    escalated_from: Optional[str] = None


# --- Connectors ---

class ConnectorStatus(BaseModel):
    connector_id: str
    enabled: bool
    last_sync: Optional[datetime] = None


class SyncRequest(BaseModel):
    date_from: Optional[date] = None
    date_to: Optional[date] = None
