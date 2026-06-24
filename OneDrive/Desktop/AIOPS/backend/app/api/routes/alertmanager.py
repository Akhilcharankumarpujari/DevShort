from __future__ import annotations

import uuid
from typing import Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permissions
from app.core.config import get_settings
from app.core.exceptions import AppException
from app.db.session import get_db_session
from app.models.user import User
from app.security.rbac import PermissionKey
from app.schemas.alertmanager import (
    AlertmanagerWebhook,
    AlertResponse,
    CorrelatedAlertIncident,
    WebhookProcessResponse,
)
from app.services.alertmanager_service import AlertmanagerService

router = APIRouter()


def get_alertmanager_service(session: AsyncSession = Depends(get_db_session)) -> AlertmanagerService:
    return AlertmanagerService(session)


@router.post("/webhook", response_model=WebhookProcessResponse)
async def process_webhook(
    webhook: AlertmanagerWebhook,
    service: AlertmanagerService = Depends(get_alertmanager_service),
    _: User = Depends(require_permissions(PermissionKey.ALERTS_WRITE)),
) -> WebhookProcessResponse:
    res = await service.process_webhook(webhook)
    return WebhookProcessResponse(
        alerts_processed=res["alerts_processed"],
        incidents_created=res["incidents_created"],
        incidents_correlated=res["incidents_correlated"],
    )


@router.get("/", response_model=list[AlertResponse])
async def list_alerts(
    status: str | None = Query(None, description="Filter by alert status"),
    severity: str | None = Query(None, description="Filter by alert severity"),
    system_id: uuid.UUID | None = Query(None, description="Filter by system ID"),
    incident_id: uuid.UUID | None = Query(None, description="Filter by incident ID"),
    namespace: str | None = Query(None, description="Filter by namespace"),
    pod: str | None = Query(None, description="Filter by pod"),
    limit: int = Query(100, ge=1, le=1000, description="Max alerts limit"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    service: AlertmanagerService = Depends(get_alertmanager_service),
    _: User = Depends(require_permissions(PermissionKey.ALERTS_READ)),
) -> list[Any]:
    return await service.get_alerts(
        status=status,
        severity=severity,
        system_id=system_id,
        incident_id=incident_id,
        namespace=namespace,
        pod=pod,
        limit=limit,
        offset=offset,
    )


@router.get("/incidents", response_model=list[CorrelatedAlertIncident])
async def list_correlated_alerts(
    service: AlertmanagerService = Depends(get_alertmanager_service),
    _: User = Depends(require_permissions(PermissionKey.ALERTS_READ)),
) -> list[Any]:
    return await service.get_correlated_alerts()


@router.get("/history", response_model=list[AlertResponse])
async def list_alerts_history(
    limit: int = Query(100, ge=1, le=1000, description="Max alerts limit"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    service: AlertmanagerService = Depends(get_alertmanager_service),
    _: User = Depends(require_permissions(PermissionKey.ALERTS_READ)),
) -> list[Any]:
    return await service.get_alerts_history(limit=limit, offset=offset)


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: uuid.UUID,
    service: AlertmanagerService = Depends(get_alertmanager_service),
    _: User = Depends(require_permissions(PermissionKey.ALERTS_READ)),
) -> Any:
    alert = await service.get_alert_by_id(alert_id)
    if not alert:
        raise AppException(
            status_code=404,
            code="alert_not_found",
            message=f"Alert with ID '{alert_id}' not found.",
        )
    return alert
