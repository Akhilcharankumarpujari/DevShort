from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.incident import Incident
    from app.models.system import System


class MetricsSource(StrEnum):
    PROMETHEUS = "prometheus"
    CLOUDWATCH = "cloudwatch"
    CUSTOM = "custom"


class MetricsSnapshot(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "metrics_snapshots"
    __table_args__ = (
        CheckConstraint(
            "source IN ('prometheus', 'cloudwatch', 'custom')",
            name="source_valid",
        ),
        CheckConstraint(
            "time_range_end >= time_range_start",
            name="time_range_valid",
        ),
        CheckConstraint(
            "step_seconds IS NULL OR step_seconds > 0",
            name="step_seconds_positive",
        ),
        Index("ix_metrics_snapshots_incident_created_at", "incident_id", "created_at"),
        Index("ix_metrics_snapshots_system_created_at", "system_id", "created_at"),
        Index("ix_metrics_snapshots_source", "source"),
        Index("ix_metrics_snapshots_deleted_at", "deleted_at"),
    )

    incident_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("incidents.id", ondelete="SET NULL"),
        nullable=True,
    )
    system_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("systems.id", ondelete="SET NULL"),
        nullable=True,
    )
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    time_range_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    time_range_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    step_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    samples: Mapped[list[dict[str, object]]] = mapped_column(JSONB, nullable=False, default=list)
    statistics: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    incident: Mapped[Incident | None] = relationship("Incident", back_populates="metrics_snapshots")
    system: Mapped[System | None] = relationship("System", back_populates="metrics_snapshots")

