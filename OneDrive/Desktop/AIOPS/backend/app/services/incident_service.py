from __future__ import annotations

import uuid
from datetime import datetime, UTC
from typing import Sequence
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.incident import Incident, IncidentStatus, IncidentSeverity, IncidentPriority
from app.models.incident_event import IncidentEvent
from app.models.audit import AuditLog, AuditActorType, AuditOutcome
from app.repositories.incident_repository import IncidentRepository
from app.schemas.incident import IncidentCreate, IncidentUpdate


class IncidentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = IncidentRepository(session)

    async def _generate_incident_number(self) -> str:
        # Generate prefix INC-YYYYMMDD-
        today_prefix = f"INC-{datetime.now(UTC).strftime('%Y%m%d')}-"
        # Find count of incidents matching this prefix
        stmt = select(func.count(Incident.id)).where(Incident.incident_number.like(f"{today_prefix}%"))
        count = await self.session.scalar(stmt) or 0
        return f"{today_prefix}{count + 1:04d}"

    def _validate_status_transition(self, current: IncidentStatus, target: IncidentStatus) -> None:
        if current == target:
            return

        allowed = {
            IncidentStatus.OPEN: [
                IncidentStatus.INVESTIGATING,
                IncidentStatus.MITIGATED,
                IncidentStatus.RESOLVED,
                IncidentStatus.CLOSED,
            ],
            IncidentStatus.INVESTIGATING: [
                IncidentStatus.MITIGATED,
                IncidentStatus.RESOLVED,
                IncidentStatus.CLOSED,
                IncidentStatus.OPEN,
            ],
            IncidentStatus.MITIGATED: [
                IncidentStatus.RESOLVED,
                IncidentStatus.CLOSED,
                IncidentStatus.INVESTIGATING,
            ],
            IncidentStatus.RESOLVED: [
                IncidentStatus.CLOSED,
                IncidentStatus.OPEN,
                IncidentStatus.INVESTIGATING,
            ],
            IncidentStatus.CLOSED: [IncidentStatus.OPEN],
        }

        if target not in allowed.get(current, []):
            raise AppException(
                status_code=400,
                code="invalid_status_transition",
                message=f"Cannot transition incident status from '{current}' to '{target}'.",
            )

    async def _log_audit_event(
        self,
        *,
        actor_id: uuid.UUID | None,
        actor_type: str,
        action: str,
        resource_id: uuid.UUID | None,
        outcome: str,
        details: dict[str, object] | None = None,
    ) -> None:
        audit = AuditLog(
            actor_id=actor_id,
            actor_type=actor_type,
            action=action,
            resource_type="incident",
            resource_id=resource_id,
            outcome=outcome,
            details=details or {},
        )
        self.session.add(audit)

    async def create_incident(self, payload: IncidentCreate, creator_id: uuid.UUID | None) -> Incident:
        incident_number = await self._generate_incident_number()
        incident = Incident(
            incident_number=incident_number,
            title=payload.title,
            description=payload.description,
            severity=payload.severity.value,
            priority=payload.priority.value,
            status=IncidentStatus.OPEN.value,
            source="manual" if creator_id else "automated",
            system_id=payload.system_id,
            created_by_id=creator_id,
            detected_at=datetime.now(UTC),
            labels=payload.labels,
        )
        
        await self.repo.create(incident)
        
        # Log Timeline Event
        event = IncidentEvent(
            incident_id=incident.id,
            event_type="incident_created",
            actor_id=creator_id,
            message="Incident created.",
            data={"title": payload.title, "severity": payload.severity.value},
        )
        await self.repo.add_event(event)

        # Log Audit Log
        await self._log_audit_event(
            actor_id=creator_id,
            actor_type=AuditActorType.USER.value if creator_id else AuditActorType.SYSTEM.value,
            action="incident:create",
            resource_id=incident.id,
            outcome=AuditOutcome.SUCCESS.value,
        )
        
        await self.session.commit()
        
        # Fetch fresh copy with loaded relationships
        return await self.repo.get_by_id(incident.id)  # type: ignore

    async def get_incident(self, incident_id: uuid.UUID) -> Incident:
        incident = await self.repo.get_by_id(incident_id)
        if not incident:
            raise AppException(
                status_code=404,
                code="incident_not_found",
                message=f"Incident with ID '{incident_id}' not found.",
            )
        return incident

    async def list_incidents(
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
        return await self.repo.get_incidents(
            status=status,
            severity=severity,
            system_id=system_id,
            assignee_id=assignee_id,
            search=search,
            detected_start=detected_start,
            detected_end=detected_end,
            page=page,
            size=size,
        )

    async def update_incident(
        self,
        incident_id: uuid.UUID,
        payload: IncidentUpdate,
        updater_id: uuid.UUID,
    ) -> Incident:
        incident = await self.get_incident(incident_id)
        
        changes: dict[str, dict[str, object]] = {}
        if payload.title is not None and payload.title != incident.title:
            changes["title"] = {"old": incident.title, "new": payload.title}
            incident.title = payload.title
        if payload.description is not None and payload.description != incident.description:
            changes["description"] = {"old": incident.description, "new": payload.description}
            incident.description = payload.description
        if payload.severity is not None and payload.severity.value != incident.severity:
            changes["severity"] = {"old": incident.severity, "new": payload.severity.value}
            incident.severity = payload.severity.value
        if payload.priority is not None and payload.priority.value != incident.priority:
            changes["priority"] = {"old": incident.priority, "new": payload.priority.value}
            incident.priority = payload.priority.value

        if changes:
            await self.repo.update(incident)
            
            # Log Timeline Event
            event = IncidentEvent(
                incident_id=incident.id,
                event_type="incident_updated",
                actor_id=updater_id,
                message="Incident details updated.",
                data={"changes": changes},
            )
            await self.repo.add_event(event)

            # Log Audit Log
            await self._log_audit_event(
                actor_id=updater_id,
                actor_type=AuditActorType.USER.value,
                action="incident:update",
                resource_id=incident.id,
                outcome=AuditOutcome.SUCCESS.value,
                details={"changes": changes},
            )
            
            await self.session.commit()
            
        return await self.repo.get_by_id(incident.id)  # type: ignore

    async def assign_incident(
        self,
        incident_id: uuid.UUID,
        assignee_id: uuid.UUID | None,
        actor_id: uuid.UUID,
    ) -> Incident:
        incident = await self.get_incident(incident_id)
        
        old_assignee_id = incident.assignee_id
        if old_assignee_id == assignee_id:
            return incident
            
        incident.assignee_id = assignee_id
        await self.repo.update(incident)
        
        # Log Timeline Event
        event = IncidentEvent(
            incident_id=incident.id,
            event_type="incident_assigned",
            actor_id=actor_id,
            message=f"Incident assignee changed.",
            data={"old_assignee_id": str(old_assignee_id) if old_assignee_id else None, "new_assignee_id": str(assignee_id) if assignee_id else None},
        )
        await self.repo.add_event(event)

        # Log Audit Log
        await self._log_audit_event(
            actor_id=actor_id,
            actor_type=AuditActorType.USER.value,
            action="incident:assign",
            resource_id=incident.id,
            outcome=AuditOutcome.SUCCESS.value,
            details={"old_assignee_id": str(old_assignee_id) if old_assignee_id else None, "new_assignee_id": str(assignee_id) if assignee_id else None},
        )
        
        await self.session.commit()
        return await self.repo.get_by_id(incident.id)  # type: ignore

    async def transition_status(
        self,
        incident_id: uuid.UUID,
        target_status: IncidentStatus,
        message: str | None,
        actor_id: uuid.UUID,
    ) -> Incident:
        incident = await self.get_incident(incident_id)
        current_status = IncidentStatus(incident.status)
        
        self._validate_status_transition(current_status, target_status)
        
        incident.status = target_status.value
        
        # Update specific timestamp columns
        now = datetime.now(UTC)
        if target_status == IncidentStatus.INVESTIGATING:
            incident.acknowledged_at = now
        elif target_status == IncidentStatus.MITIGATED:
            incident.mitigated_at = now
        elif target_status == IncidentStatus.RESOLVED:
            incident.resolved_at = now
        elif target_status == IncidentStatus.CLOSED:
            incident.closed_at = now
            
        await self.repo.update(incident)
        
        # Log Timeline Event
        event_message = f"Incident status transitioned from '{current_status.value}' to '{target_status.value}'."
        if message:
            event_message += f" Reason: {message}"
            
        event = IncidentEvent(
            incident_id=incident.id,
            event_type="status_changed",
            actor_id=actor_id,
            message=event_message,
            data={"old_status": current_status.value, "new_status": target_status.value, "comment": message},
        )
        await self.repo.add_event(event)

        # Log Audit Log
        await self._log_audit_event(
            actor_id=actor_id,
            actor_type=AuditActorType.USER.value,
            action="incident:transition_status",
            resource_id=incident.id,
            outcome=AuditOutcome.SUCCESS.value,
            details={"old_status": current_status.value, "new_status": target_status.value},
        )
        
        await self.session.commit()
        return await self.repo.get_by_id(incident.id)  # type: ignore

    async def delete_incident(self, incident_id: uuid.UUID, actor_id: uuid.UUID) -> None:
        incident = await self.get_incident(incident_id)
        
        incident.deleted_at = datetime.now(UTC)
        await self.repo.update(incident)
        
        # Log Audit Log
        await self._log_audit_event(
            actor_id=actor_id,
            actor_type=AuditActorType.USER.value,
            action="incident:delete",
            resource_id=incident.id,
            outcome=AuditOutcome.SUCCESS.value,
        )
        
        await self.session.commit()

    async def get_incident_timeline(self, incident_id: uuid.UUID) -> Sequence[IncidentEvent]:
        # Validate that incident exists first
        await self.get_incident(incident_id)
        return await self.repo.get_timeline(incident_id)
