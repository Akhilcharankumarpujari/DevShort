"""create aiops domain tables

Revision ID: 20260624_0002
Revises: 20260624_0001
Create Date: 2026-06-24 00:02:00.000000
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260624_0002"
down_revision: str | None = "20260624_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.create_check_constraint(
        op.f("ck_users_status_valid"),
        "users",
        "status IN ('active', 'disabled', 'pending')",
    )
    op.create_index("ix_users_deleted_at", "users", ["deleted_at"], unique=False)

    op.create_table(
        "systems",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("system_type", sa.String(length=32), nullable=False),
        sa.Column("environment", sa.String(length=32), nullable=False),
        sa.Column("criticality", sa.String(length=32), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("external_ref", sa.String(length=255), nullable=True),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "system_type IN ('service', 'application', 'cluster', 'namespace', "
            "'infrastructure', 'database', 'pipeline', 'other')",
            name=op.f("ck_systems_system_type_valid"),
        ),
        sa.CheckConstraint(
            "environment IN ('production', 'staging', 'development', 'test', 'local', 'unknown')",
            name=op.f("ck_systems_environment_valid"),
        ),
        sa.CheckConstraint(
            "criticality IN ('critical', 'high', 'medium', 'low')",
            name=op.f("ck_systems_criticality_valid"),
        ),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], name=op.f("fk_systems_owner_id_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_systems")),
        sa.UniqueConstraint("slug", name="uq_systems_slug"),
    )
    op.create_index("ix_systems_deleted_at", "systems", ["deleted_at"], unique=False)
    op.create_index("ix_systems_owner_id", "systems", ["owner_id"], unique=False)
    op.create_index("ix_systems_type_environment", "systems", ["system_type", "environment"], unique=False)

    op.create_table(
        "incidents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("incident_number", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("priority", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=True),
        sa.Column("system_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("assignee_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("mitigated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("labels", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("severity IN ('sev1', 'sev2', 'sev3', 'sev4')", name=op.f("ck_incidents_severity_valid")),
        sa.CheckConstraint("priority IN ('p1', 'p2', 'p3', 'p4')", name=op.f("ck_incidents_priority_valid")),
        sa.CheckConstraint(
            "status IN ('open', 'investigating', 'mitigated', 'resolved', 'closed')",
            name=op.f("ck_incidents_status_valid"),
        ),
        sa.ForeignKeyConstraint(["assignee_id"], ["users.id"], name=op.f("fk_incidents_assignee_id_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], name=op.f("fk_incidents_created_by_id_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["system_id"], ["systems.id"], name=op.f("fk_incidents_system_id_systems"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_incidents")),
        sa.UniqueConstraint("incident_number", name="uq_incidents_incident_number"),
    )
    op.create_index("ix_incidents_assignee_status", "incidents", ["assignee_id", "status"], unique=False)
    op.create_index("ix_incidents_deleted_at", "incidents", ["deleted_at"], unique=False)
    op.create_index("ix_incidents_status_severity", "incidents", ["status", "severity"], unique=False)
    op.create_index("ix_incidents_system_detected_at", "incidents", ["system_id", "detected_at"], unique=False)

    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("fingerprint", sa.String(length=255), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("system_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("labels", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("annotations", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("severity IN ('critical', 'warning', 'info')", name=op.f("ck_alerts_severity_valid")),
        sa.CheckConstraint("status IN ('firing', 'resolved', 'acknowledged', 'suppressed')", name=op.f("ck_alerts_status_valid")),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"], name=op.f("fk_alerts_incident_id_incidents"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["system_id"], ["systems.id"], name=op.f("fk_alerts_system_id_systems"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_alerts")),
        sa.UniqueConstraint("fingerprint", name="uq_alerts_fingerprint"),
        sa.UniqueConstraint("source", "external_id", name="uq_alerts_source_external_id"),
    )
    op.create_index("ix_alerts_deleted_at", "alerts", ["deleted_at"], unique=False)
    op.create_index("ix_alerts_incident_id", "alerts", ["incident_id"], unique=False)
    op.create_index("ix_alerts_status_severity", "alerts", ["status", "severity"], unique=False)
    op.create_index("ix_alerts_system_starts_at", "alerts", ["system_id", "starts_at"], unique=False)
