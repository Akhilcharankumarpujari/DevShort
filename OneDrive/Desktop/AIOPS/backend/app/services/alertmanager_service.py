from __future__ import annotations

import logging
import uuid
from datetime import datetime, UTC
from typing import Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert, AlertStatus, AlertSeverity
from app.models.system import System
from app.models.incident import Incident, IncidentStatus, IncidentSeverity, IncidentPriority
from app.models.incident_event import IncidentEvent
from app.schemas.alertmanager import AlertmanagerWebhook

logger = logging.getLogger(__name__)


class AlertmanagerService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _find_system(self, labels: dict[str, str]) -> uuid.UUID | None:
        # Check system, service, app labels to find a system record
        for key in ["system", "service", "app", "application", "slug"]:
            val = labels.get(key)
            if val:
                stmt = select(System).where(
                    (System.slug == val.lower()) | (System.name.ilike(val)),
                    System.deleted_at.is_(None),
                )
                res = await self.session.execute(stmt)
                sys = res.scalars().first()
                if sys:
                    return sys.id
        return None

    async def _check_and_escalate_severity(
        self,
        incident: Incident,
        alert_sev: str,
        alert_title: str,
    ) -> None:
        # Severity rank: higher is more severe
        rank = {
            "sev4": 1,
            "sev3": 2,
            "sev2": 3,
            "sev1": 4,
        }

        # Map alert severity to incident severity
        alert_mapped_sev = "sev3"
        alert_mapped_pri = "p3"
        if alert_sev == "critical":
            alert_mapped_sev = "sev1"
            alert_mapped_pri = "p1"
        elif alert_sev == "warning":
            alert_mapped_sev = "sev2"
            alert_mapped_pri = "p2"
        elif alert_sev == "info":
            alert_mapped_sev = "sev4"
            alert_mapped_pri = "p4"

        current_rank = rank.get(incident.severity, 0)
        new_rank = rank.get(alert_mapped_sev, 0)

        if new_rank > current_rank:
            old_sev = incident.severity
            old_pri = incident.priority
            incident.severity = alert_mapped_sev
            incident.priority = alert_mapped_pri

            # Log timeline event
            event = IncidentEvent(
                incident_id=incident.id,
                event_type="incident_escalated",
                actor_id=None,
                message=f"Incident severity escalated from '{old_sev}' to '{alert_mapped_sev}' due to alert '{alert_title}'.",
                data={
                    "old_severity": old_sev,
                    "new_severity": alert_mapped_sev,
                    "old_priority": old_pri,
                    "new_priority": alert_mapped_pri,
                },
            )
            self.session.add(event)

    async def process_webhook(self, webhook: AlertmanagerWebhook) -> dict[str, int]:
        alerts_processed = 0
        incidents_created = 0
        incidents_correlated = 0

        # We will need IncidentService to auto-create incidents
        from app.services.incident_service import IncidentService
        from app.schemas.incident import IncidentCreate

        for alert_data in webhook.alerts:
            alerts_processed += 1
            fingerprint = alert_data.fingerprint

            # Map alert severity to database check-constrained strings: "critical", "warning", "info"
            raw_sev = alert_data.labels.get("severity", "info").lower()
            mapped_sev = "info"
            if raw_sev in ["critical", "crit", "fatal", "error", "err"]:
                mapped_sev = "critical"
            elif raw_sev in ["warning", "warn", "high", "medium"]:
                mapped_sev = "warning"

            status = AlertStatus.FIRING.value
            if alert_data.status == "resolved":
                status = AlertStatus.RESOLVED.value

            title = alert_data.labels.get("alertname", "Alertmanager Alert")
            description = (
                alert_data.annotations.get("description")
                or alert_data.annotations.get("summary")
                or f"Alertmanager alert: {title}"
            )
            starts_at = alert_data.startsAt
            ends_at = alert_data.endsAt

            # Check if alert already exists
            stmt = select(Alert).where(Alert.fingerprint == fingerprint, Alert.deleted_at.is_(None))
            res = await self.session.execute(stmt)
            db_alert = res.scalars().first()

            system_id = await self._find_system(alert_data.labels)

            if db_alert:
                db_alert.status = status
                db_alert.severity = mapped_sev
                db_alert.title = title
                db_alert.description = description
                db_alert.starts_at = starts_at
                db_alert.ends_at = ends_at
                db_alert.labels = alert_data.labels
                db_alert.annotations = alert_data.annotations
                db_alert.raw_payload = alert_data.model_dump()
                if system_id:
                    db_alert.system_id = system_id
                alert_obj = db_alert
            else:
                alert_obj = Alert(
                    source="alertmanager",
                    external_id=fingerprint,
                    fingerprint=fingerprint,
                    title=title,
                    description=description,
                    severity=mapped_sev,
                    status=status,
                    system_id=system_id,
                    starts_at=starts_at,
                    ends_at=ends_at,
                    labels=alert_data.labels,
                    annotations=alert_data.annotations,
                    raw_payload=alert_data.model_dump(),
                )
                self.session.add(alert_obj)
                await self.session.flush()

            # Handle resolution / correlation
            if status == AlertStatus.RESOLVED.value:
                if alert_obj.incident_id:
                    stmt_firing = select(func.count(Alert.id)).where(
                        Alert.incident_id == alert_obj.incident_id,
                        Alert.status == AlertStatus.FIRING.value,
                        Alert.id != alert_obj.id,
                        Alert.deleted_at.is_(None),
                    )
                    firing_count = await self.session.scalar(stmt_firing) or 0
                    if firing_count == 0:
                        # Auto-resolve incident
                        stmt_inc = select(Incident).where(Incident.id == alert_obj.incident_id)
                        res_inc = await self.session.execute(stmt_inc)
                        incident = res_inc.scalars().first()
                        if incident and incident.status != IncidentStatus.RESOLVED.value:
                            incident.status = IncidentStatus.RESOLVED.value
                            incident.resolved_at = datetime.now(UTC)

                            event = IncidentEvent(
                                incident_id=incident.id,
                                event_type="status_changed",
                                actor_id=None,
                                message="Incident resolved automatically as all associated alerts are resolved.",
                                data={"old_status": incident.status, "new_status": IncidentStatus.RESOLVED.value},
                            )
                            self.session.add(event)
            else:
                # status is firing
                correlated = False
                if alert_obj.incident_id:
                    stmt_inc = select(Incident).where(Incident.id == alert_obj.incident_id)
                    res_inc = await self.session.execute(stmt_inc)
                    incident = res_inc.scalars().first()
                    if incident and incident.status in [
                        IncidentStatus.OPEN.value,
                        IncidentStatus.INVESTIGATING.value,
                        IncidentStatus.MITIGATED.value,
                    ]:
                        correlated = True
                        incidents_correlated += 1
                        await self._check_and_escalate_severity(incident, mapped_sev, title)

                if not correlated:
                    stmt_active = select(Incident).where(
                        Incident.status.in_(
                            [
                                IncidentStatus.OPEN.value,
                                IncidentStatus.INVESTIGATING.value,
                                IncidentStatus.MITIGATED.value,
                            ]
                        ),
                        Incident.deleted_at.is_(None),
                    )
                    res_active = await self.session.execute(stmt_active)
                    active_incidents = res_active.scalars().all()

                    matched_incident = None
                    pod = alert_data.labels.get("pod")
                    deployment = alert_data.labels.get("deployment")
                    namespace = alert_data.labels.get("namespace")

                    for inc in active_incidents:
                        inc_pod = inc.labels.get("pod")
                        inc_deployment = inc.labels.get("deployment")
                        inc_namespace = inc.labels.get("namespace")

                        if pod and pod == inc_pod:
                            matched_incident = inc
                            break
                        elif deployment and deployment == inc_deployment:
                            matched_incident = inc
                            break
                        elif namespace and namespace == inc_namespace:
                            matched_incident = inc
                            break
                        elif system_id and system_id == inc.system_id:
                            matched_incident = inc
                            break

                    if matched_incident:
                        alert_obj.incident_id = matched_incident.id
                        incidents_correlated += 1

                        event = IncidentEvent(
                            incident_id=matched_incident.id,
                            event_type="alert_correlated",
                            actor_id=None,
                            message=f"Alert '{title}' (fingerprint: {fingerprint}) correlated to this incident.",
                            data={"alert_id": str(alert_obj.id), "fingerprint": fingerprint, "severity": mapped_sev},
                        )
                        self.session.add(event)
                        await self._check_and_escalate_severity(matched_incident, mapped_sev, title)
                    else:
                        incidents_created += 1

                        inc_sev = IncidentSeverity.SEV3
                        inc_pri = IncidentPriority.P3
                        if mapped_sev == "critical":
                            inc_sev = IncidentSeverity.SEV1
                            inc_pri = IncidentPriority.P1
                        elif mapped_sev == "warning":
                            inc_sev = IncidentSeverity.SEV2
                            inc_pri = IncidentPriority.P2
                        else:
                            inc_sev = IncidentSeverity.SEV4
                            inc_pri = IncidentPriority.P4

                        inc_service = IncidentService(self.session)
                        inc_create = IncidentCreate(
                            title=f"Alert Triggered: {title}",
                            description=f"Automated incident created from alert: {title}\nDescription: {description}",
                            severity=inc_sev,
                            priority=inc_pri,
                            system_id=system_id,
                            labels=alert_data.labels,
                        )
                        new_incident = await inc_service.create_incident(inc_create, creator_id=None)
                        alert_obj.incident_id = new_incident.id

                        event = IncidentEvent(
                            incident_id=new_incident.id,
                            event_type="alert_correlated",
                            actor_id=None,
                            message=f"Initial alert '{title}' (fingerprint: {fingerprint}) correlated to this incident.",
                            data={"alert_id": str(alert_obj.id), "fingerprint": fingerprint, "severity": mapped_sev},
                        )
                        self.session.add(event)

        await self.session.commit()
        return {
            "alerts_processed": alerts_processed,
            "incidents_created": incidents_created,
            "incidents_correlated": incidents_correlated,
        }

    async def get_alerts(
        self,
        *,
        status: str | None = None,
        severity: str | None = None,
        system_id: uuid.UUID | None = None,
        incident_id: uuid.UUID | None = None,
        namespace: str | None = None,
        pod: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Alert]:
        stmt = select(Alert).where(Alert.deleted_at.is_(None))
        if status:
            stmt = stmt.where(Alert.status == status)
        if severity:
            stmt = stmt.where(Alert.severity == severity)
        if system_id:
            stmt = stmt.where(Alert.system_id == system_id)
        if incident_id:
            stmt = stmt.where(Alert.incident_id == incident_id)
        if namespace:
            stmt = stmt.where(Alert.labels["namespace"].as_string() == namespace)
        if pod:
            stmt = stmt.where(Alert.labels["pod"].as_string() == pod)

        stmt = stmt.order_by(Alert.starts_at.desc()).offset(offset).limit(limit)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_alert_by_id(self, alert_id: uuid.UUID) -> Alert | None:
        stmt = select(Alert).where(Alert.id == alert_id, Alert.deleted_at.is_(None))
        res = await self.session.execute(stmt)
        return res.scalars().first()

    async def get_correlated_alerts(self) -> list[dict[str, Any]]:
        stmt = (
            select(Alert, Incident)
            .join(Incident, Alert.incident_id == Incident.id)
            .where(Alert.deleted_at.is_(None), Incident.deleted_at.is_(None))
            .order_by(Alert.updated_at.desc())
        )
        res = await self.session.execute(stmt)
        results = res.all()

        correlated = []
        for alert, incident in results:
            correlated.append(
                {
                    "alert_id": alert.id,
                    "fingerprint": alert.fingerprint,
                    "title": alert.title,
                    "incident_id": incident.id,
                    "incident_number": incident.incident_number,
                    "incident_title": incident.title,
                    "incident_status": incident.status,
                }
            )
        return correlated

    async def get_alerts_history(self, limit: int = 100, offset: int = 0) -> list[Alert]:
        stmt = (
            select(Alert)
            .where(Alert.deleted_at.is_(None))
            .order_by(Alert.starts_at.desc())
            .offset(offset)
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())
