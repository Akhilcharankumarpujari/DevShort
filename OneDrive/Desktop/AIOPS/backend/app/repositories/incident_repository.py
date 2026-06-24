from __future__ import annotations

import uuid
from datetime import datetime
from typing import Sequence
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.incident import Incident, IncidentStatus, IncidentSeverity
from app.models.incident_event import IncidentEvent
from app.models.system import System
from app.models.user import User


class IncidentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, incident_id: uuid.UUID) -> Incident | None:
        stmt = (
            select(Incident)
            .options(
                selectinload(Incident.system),
                selectinload(Incident.assignee),
                selectinload(Incident.created_by_user),
            )
            .where(Incident.id == incident_id, Incident.deleted_at.is_(None))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_number(self, incident_number: str) -> Incident | None:
        stmt = (
            select(Incident)
            .options(
                selectinload(Incident.system),
                selectinload(Incident.assignee),
                selectinload(Incident.created_by_user),
            )
            .where(Incident.incident_number == incident_number, Incident.deleted_at.is_(None))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_incidents(
        self,
        *,
        status: list[IncidentStatus] | None = None,
        severity: list[IncidentSeverity] | None = None,
        system_id: uuid.UUID | None = None,
        assignee_id: uuid.UUID | None = None,
        search: str | None = None,
        detected_start: datetime | None = None,
        detected_end: datetime | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[Sequence[Incident], int]:
        # Build base select statement
        stmt = select(Incident).where(Incident.deleted_at.is_(None))

        # Filtering
        if status:
            stmt = stmt.where(Incident.status.in_([s.value for s in status]))
        if severity:
            stmt = stmt.where(Incident.severity.in_([s.value for s in severity]))
        if system_id:
            stmt = stmt.where(Incident.system_id == system_id)
        if assignee_id:
            stmt = stmt.where(Incident.assignee_id == assignee_id)
        if detected_start:
            stmt = stmt.where(Incident.detected_at >= detected_start)
        if detected_end:
            stmt = stmt.where(Incident.detected_at <= detected_end)

        # Search Query (matches title, description, or incident_number)
        if search:
            search_pattern = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Incident.title.ilike(search_pattern),
                    Incident.description.ilike(search_pattern),
                    Incident.incident_number.ilike(search_pattern),
                )
            )

        # Count total matches before pagination
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await self.session.scalar(count_stmt) or 0

        # Pagination & Eager Loading
        offset = (page - 1) * size
        stmt = (
            stmt.options(
                selectinload(Incident.system),
                selectinload(Incident.assignee),
                selectinload(Incident.created_by_user),
            )
            .order_by(Incident.created_at.desc())  # Default order
            .offset(offset)
            .limit(size)
        )
        
        result = await self.session.execute(stmt)
        return result.scalars().all(), total

    async def create(self, incident: Incident) -> Incident:
        self.session.add(incident)
        await self.session.flush()
        return incident

    async def update(self, incident: Incident) -> Incident:
        await self.session.flush()
        return incident

    # Incident Timeline Events Repository operations
    async def add_event(self, event: IncidentEvent) -> IncidentEvent:
        self.session.add(event)
        await self.session.flush()
        return event

    async def get_timeline(self, incident_id: uuid.UUID) -> Sequence[IncidentEvent]:
        stmt = (
            select(IncidentEvent)
            .options(selectinload(IncidentEvent.actor))
            .where(IncidentEvent.incident_id == incident_id, IncidentEvent.deleted_at.is_(None))
            .order_by(IncidentEvent.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
