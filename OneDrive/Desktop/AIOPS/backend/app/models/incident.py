from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.system import System
    from app.models.user import User
    from app.models.alert import Alert
    from app.models.analysis import Analysis
    from app.models.remediation import RemediationAction
    from app.models.metrics import MetricsSnapshot
    from app.models.incident_event import IncidentEvent


class IncidentSeverity(StrEnum):
    SEV1 = "sev1"
    SEV2 = "sev2"
    SEV3 = "sev3"
    SEV4 = "sev4"


class IncidentPriority(StrEnum):
    P1 = "p1"
    P2 = "p2"
    P3 = "p3"
    P4 = "p4"


class IncidentStatus(StrEnum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    MITIGATED = "mitigated"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Incident(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "incidents"
    __table_args__ = (
        CheckConstraint(
            "severity IN ('sev1', 'sev2', 'sev3', 'sev4')",
            name="severity_valid",
        ),
        CheckConstraint("priority IN ('p1', 'p2', 'p3', 'p4')", name="priority_valid"),
        CheckConstraint(
            "status IN ('open', 'investigating', 'mitigated', 'resolved', 'closed')",
            name="status_valid",
        ),
        UniqueConstraint("incident_number", name="uq_incidents_incident_number"),
        Index("ix_incidents_status_severity", "status", "severity"),
        Index("ix_incidents_system_detected_at", "system_id", "detected_at"),
        Index("ix_incidents_assignee_status", "assignee_id", "status"),
        Index("ix_incidents_deleted_at", "deleted_at"),
    )

    incident_number: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    priority: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=IncidentStatus.OPEN.value)
    source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    system_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("systems.id", ondelete="SET NULL"),
        nullable=True,
    )
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    mitigated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    labels: Mapped[dict[str, str]] = mapped_column(JSONB, nullable=False, default=dict)

    system: Mapped[System | None] = relationship("System", back_populates="incidents")
    assignee: Mapped[User | None] = relationship(
        "User",
        back_populates="assigned_incidents",
        foreign_keys=[assignee_id],
    )
    created_by_user: Mapped[User | None] = relationship(
        "User",
        back_populates="created_incidents",
        foreign_keys=[created_by_id],
    )
    alerts: Mapped[list[Alert]] = relationship("Alert", back_populates="incident")
    analyses: Mapped[list[Analysis]] = relationship("Analysis", back_populates="incident")
    remediation_actions: Mapped[list[RemediationAction]] = relationship(
        "RemediationAction",
        back_populates="incident",
    )
    metrics_snapshots: Mapped[list[MetricsSnapshot]] = relationship(
        "MetricsSnapshot",
        back_populates="incident",
    )
    events: Mapped[list[IncidentEvent]] = relationship(
        "IncidentEvent",
        back_populates="incident",
        cascade="all, delete-orphan",
    )

