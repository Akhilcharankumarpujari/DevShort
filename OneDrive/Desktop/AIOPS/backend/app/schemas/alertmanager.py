from __future__ import annotations

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class AlertmanagerAlert(BaseModel):
    status: str  # "firing" or "resolved"
    labels: dict[str, str]
    annotations: dict[str, str]
    startsAt: datetime
    endsAt: datetime | None = None
    generatorURL: str | None = None
    fingerprint: str


class AlertmanagerWebhook(BaseModel):
    receiver: str
    status: str
    alerts: list[AlertmanagerAlert]
    groupLabels: dict[str, str] = Field(default_factory=dict)
    commonLabels: dict[str, str] = Field(default_factory=dict)
    commonAnnotations: dict[str, str] = Field(default_factory=dict)
    externalURL: str | None = None
    version: str
    groupKey: str | None = None


class AlertResponse(BaseModel):
    id: UUID
    source: str
    external_id: str | None = None
    fingerprint: str | None = None
    title: str
    description: str | None = None
    severity: str
    status: str
    system_id: UUID | None = None
    incident_id: UUID | None = None
    starts_at: datetime
    ends_at: datetime | None = None
    labels: dict[str, str]
    annotations: dict[str, str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CorrelatedAlertIncident(BaseModel):
    alert_id: UUID
    fingerprint: str | None = None
    title: str
    incident_id: UUID
    incident_number: str
    incident_title: str
    incident_status: str

    class Config:
        from_attributes = True


class WebhookProcessResponse(BaseModel):
    alerts_processed: int
    incidents_created: int
    incidents_correlated: int
    status: str = "processed"
