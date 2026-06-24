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
    from app.models.incident import Incident


class AlertSeverity(StrEnum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class AlertStatus(StrEnum):
    FIRING = "firing"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"
    SUPPRESSED = "suppressed"


class Alert(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "alerts"
    __table_args__ = (
        CheckConstraint(
            "severity IN ('critical', 'warning', 'info')",
            name="severity_valid",
        ),
        CheckConstraint(
            "status IN ('firing', 'resolved', 'acknowledged', 'suppressed')",
            name="status_valid",
        ),
        UniqueConstraint("source", "external_id", name="uq_alerts_source_external_id"),
        UniqueConstraint("fingerprint", name="uq_alerts_fingerprint"),
        Index("ix_alerts_status_severity", "status", "severity"),
        Index("ix_alerts_system_starts_at", "system_id", "starts_at"),
        Index("ix_alerts_incident_id", "incident_id"),
        Index("ix_alerts_deleted_at", "deleted_at"),
    )

    source: Mapped[str] = mapped_column(String(64), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fingerprint: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=AlertStatus.FIRING.value)
    system_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("systems.id", ondelete="SET NULL"),
        nullable=True,
    )
    incident_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("incidents.id", ondelete="SET NULL"),
        nullable=True,
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    labels: Mapped[dict[str, str]] = mapped_column(JSONB, nullable=False, default=dict)
    annotations: Mapped[dict[str, str]] = mapped_column(JSONB, nullable=False, default=dict)
    raw_payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)

    system: Mapped[System | None] = relationship("System", back_populates="alerts")
    incident: Mapped[Incident | None] = relationship("Incident", back_populates="alerts")

