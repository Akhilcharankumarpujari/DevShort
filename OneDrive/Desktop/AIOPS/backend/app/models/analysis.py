from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.incident import Incident
    from app.models.system import System
    from app.models.user import User
    from app.models.remediation import RemediationAction


class AnalysisType(StrEnum):
    RCA = "rca"
    LOG = "log"
    METRIC = "metric"
    ANOMALY = "anomaly"
    REMEDIATION = "remediation"
    MANUAL = "manual"


class AnalysisStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Analysis(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "analyses"
    __table_args__ = (
        CheckConstraint(
            "analysis_type IN ('rca', 'log', 'metric', 'anomaly', 'remediation', 'manual')",
            name="analysis_type_valid",
        ),
        CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed')",
            name="status_valid",
        ),
        CheckConstraint(
            "confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 1)",
            name="confidence_score_valid",
        ),
        Index("ix_analyses_incident_created_at", "incident_id", "created_at"),
        Index("ix_analyses_system_created_at", "system_id", "created_at"),
        Index("ix_analyses_status", "status"),
        Index("ix_analyses_deleted_at", "deleted_at"),
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
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    analysis_type: Mapped[str] = mapped_column(String(32), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=AnalysisStatus.PENDING.value)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    evidence: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    recommendations: Mapped[list[dict[str, object]]] = mapped_column(JSONB, nullable=False, default=list)
    prompt_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    token_usage: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    incident: Mapped[Incident | None] = relationship("Incident", back_populates="analyses")
    system: Mapped[System | None] = relationship("System", back_populates="analyses")
    created_by_user: Mapped[User | None] = relationship("User", back_populates="analyses")
    remediation_actions: Mapped[list[RemediationAction]] = relationship(
        "RemediationAction",
        back_populates="analysis",
    )

