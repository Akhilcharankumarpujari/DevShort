from __future__ import annotations

import uuid
from enum import StrEnum

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.incident import Incident
    from app.models.alert import Alert
    from app.models.analysis import Analysis
    from app.models.remediation import RemediationAction
    from app.models.metrics import MetricsSnapshot


class SystemType(StrEnum):
    SERVICE = "service"
    APPLICATION = "application"
    CLUSTER = "cluster"
    NAMESPACE = "namespace"
    INFRASTRUCTURE = "infrastructure"
    DATABASE = "database"
    PIPELINE = "pipeline"
    OTHER = "other"


class SystemEnvironment(StrEnum):
    PRODUCTION = "production"
    STAGING = "staging"
    DEVELOPMENT = "development"
    TEST = "test"
    LOCAL = "local"
    UNKNOWN = "unknown"


class SystemCriticality(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class System(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "systems"
    __table_args__ = (
        CheckConstraint(
            "system_type IN ('service', 'application', 'cluster', 'namespace', "
            "'infrastructure', 'database', 'pipeline', 'other')",
            name="system_type_valid",
        ),
        CheckConstraint(
            "environment IN ('production', 'staging', 'development', 'test', 'local', 'unknown')",
            name="environment_valid",
        ),
        CheckConstraint(
            "criticality IN ('critical', 'high', 'medium', 'low')",
            name="criticality_valid",
        ),
        UniqueConstraint("slug", name="uq_systems_slug"),
        Index("ix_systems_owner_id", "owner_id"),
        Index("ix_systems_type_environment", "system_type", "environment"),
        Index("ix_systems_deleted_at", "deleted_at"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    system_type: Mapped[str] = mapped_column(String(32), nullable=False)
    environment: Mapped[str] = mapped_column(String(32), nullable=False, default=SystemEnvironment.UNKNOWN.value)
    criticality: Mapped[str] = mapped_column(String(32), nullable=False, default=SystemCriticality.MEDIUM.value)
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    external_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tags: Mapped[dict[str, str]] = mapped_column(JSONB, nullable=False, default=dict)
    extra_metadata: Mapped[dict[str, object]] = mapped_column("metadata", JSONB, nullable=False, default=dict)

    owner: Mapped[User | None] = relationship(
        "User",
        back_populates="owned_systems",
        foreign_keys=[owner_id],
    )
    incidents: Mapped[list[Incident]] = relationship("Incident", back_populates="system")
    alerts: Mapped[list[Alert]] = relationship("Alert", back_populates="system")
    analyses: Mapped[list[Analysis]] = relationship("Analysis", back_populates="system")
    remediation_actions: Mapped[list[RemediationAction]] = relationship(
        "RemediationAction",
        back_populates="system",
    )
    metrics_snapshots: Mapped[list[MetricsSnapshot]] = relationship(
        "MetricsSnapshot",
        back_populates="system",
    )

