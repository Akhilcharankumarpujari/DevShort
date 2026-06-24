from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.incident import Incident
    from app.models.analysis import Analysis
    from app.models.system import System
    from app.models.user import User


class RemediationActionType(StrEnum):
    KUBERNETES = "kubernetes"
    JENKINS = "jenkins"
    AWS = "aws"
    SCRIPT = "script"
    MANUAL = "manual"
    NOTIFICATION = "notification"


class RemediationRiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RemediationStatus(StrEnum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class RemediationAction(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "remediation_actions"
    __table_args__ = (
        CheckConstraint(
            "action_type IN ('kubernetes', 'jenkins', 'aws', 'script', 'manual', 'notification')",
            name="action_type_valid",
        ),
        CheckConstraint(
            "risk_level IN ('low', 'medium', 'high', 'critical')",
            name="risk_level_valid",
        ),
        CheckConstraint(
            "status IN ('pending_approval', 'approved', 'running', 'succeeded', "
            "'failed', 'cancelled', 'rejected')",
            name="status_valid",
        ),
        Index("ix_remediation_actions_incident_status", "incident_id", "status"),
        Index("ix_remediation_actions_analysis_id", "analysis_id"),
        Index("ix_remediation_actions_system_id", "system_id"),
        Index("ix_remediation_actions_requested_by_id", "requested_by_id"),
        Index("ix_remediation_actions_deleted_at", "deleted_at"),
    )

    incident_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("incidents.id", ondelete="SET NULL"),
        nullable=True,
    )
    analysis_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("analyses.id", ondelete="SET NULL"),
        nullable=True,
    )
    system_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("systems.id", ondelete="SET NULL"),
        nullable=True,
    )
    requested_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    action_type: Mapped[str] = mapped_column(String(32), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=RemediationStatus.PENDING_APPROVAL.value,
    )
    requires_approval: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    parameters: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    result: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    incident: Mapped[Incident | None] = relationship("Incident", back_populates="remediation_actions")
    analysis: Mapped[Analysis | None] = relationship("Analysis", back_populates="remediation_actions")
    system: Mapped[System | None] = relationship("System", back_populates="remediation_actions")
    requested_by_user: Mapped[User | None] = relationship(
        "User",
        back_populates="remediation_actions",
        foreign_keys=[requested_by_id],
    )
    approved_by_user: Mapped[User | None] = relationship("User", foreign_keys=[approved_by_id])

