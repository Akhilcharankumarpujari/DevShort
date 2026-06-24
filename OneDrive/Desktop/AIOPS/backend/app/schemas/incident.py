from __future__ import annotations

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr
from app.models.incident import IncidentSeverity, IncidentPriority, IncidentStatus

# User summary schema to embed in responses
class UserSummary(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str

    class Config:
        from_attributes = True

# System summary schema to embed in responses
class SystemSummary(BaseModel):
    id: UUID
    name: str
    slug: str

    class Config:
        from_attributes = True

# Incident Event response schema
class IncidentEventResponse(BaseModel):
    id: UUID
    incident_id: UUID
    event_type: str
    actor_id: UUID | None
    actor: UserSummary | None
    message: str
    data: dict[str, object]
    created_at: datetime

    class Config:
        from_attributes = True

# Incident creation payload
class IncidentCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str | None = None
    severity: IncidentSeverity = IncidentSeverity.SEV3
    priority: IncidentPriority = IncidentPriority.P3
    system_id: UUID | None = None
    labels: dict[str, str] = Field(default_factory=dict)

# Incident update payload
class IncidentUpdate(BaseModel):
    title: str | None = Field(None, min_length=3, max_length=255)
    description: str | None = None
    severity: IncidentSeverity | None = None
    priority: IncidentPriority | None = None

# Incident assignment payload
class IncidentAssign(BaseModel):
    assignee_id: UUID | None = None  # None unassigns the incident

# Incident status transition payload
class IncidentStatusTransition(BaseModel):
    status: IncidentStatus
    message: str | None = None  # Custom comment/reason for transition

# Incident response detail
class IncidentDetailResponse(BaseModel):
    id: UUID
    incident_number: str
    title: str
    description: str | None
    severity: IncidentSeverity
    priority: IncidentPriority
    status: IncidentStatus
    source: str | None
    system_id: UUID | None
    system: SystemSummary | None
    assignee_id: UUID | None
    assignee: UserSummary | None
    created_by_id: UUID | None
    created_by_user: UserSummary | None
    detected_at: datetime
    acknowledged_at: datetime | None
    mitigated_at: datetime | None
    resolved_at: datetime | None
    closed_at: datetime | None
    labels: dict[str, str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Paginated list wrapper
class IncidentListResponse(BaseModel):
    items: list[IncidentDetailResponse]
    total: int
    page: int
    size: int
    pages: int
