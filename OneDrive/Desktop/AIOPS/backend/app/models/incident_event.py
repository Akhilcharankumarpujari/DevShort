from __future__ import annotations

import uuid
from sqlalchemy import ForeignKey, Index, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.incident import Incident
    from app.models.user import User


class IncidentEvent(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "incident_events"
    __table_args__ = (
        Index("ix_incident_events_incident_created_at", "incident_id", "created_at"),
        Index("ix_incident_events_deleted_at", "deleted_at"),
    )

    incident_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)

    incident: Mapped[Incident] = relationship("Incident", back_populates="events")
    actor: Mapped[User | None] = relationship("User")
