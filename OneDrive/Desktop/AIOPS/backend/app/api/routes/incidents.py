from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, Depends, Query, Path, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, require_permissions
from app.db.session import get_db_session
from app.models.user import User
from app.models.incident import IncidentStatus, IncidentSeverity
from app.security.rbac import PermissionKey
from app.services.incident_service import IncidentService
from app.schemas.incident import (
    IncidentCreate,
    IncidentUpdate,
    IncidentAssign,
    IncidentStatusTransition,
    IncidentDetailResponse,
    IncidentListResponse,
    IncidentEventResponse,
)

router = APIRouter()


@router.post(
    "/",
    response_model=IncidentDetailResponse,
    status_code=201,
    dependencies=[Depends(require_permissions(PermissionKey.INCIDENTS_CREATE))],
)
async def create_incident(
    payload: IncidentCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> IncidentDetailResponse:
    service = IncidentService(session)
    incident = await service.create_incident(payload, current_user.id)
    return IncidentDetailResponse.model_validate(incident)


@router.get(
    "/",
    response_model=IncidentListResponse,
    dependencies=[Depends(require_permissions(PermissionKey.INCIDENTS_READ))],
)
async def list_incidents(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    status: list[IncidentStatus] | None = Query(None),
    severity: list[IncidentSeverity] | None = Query(None),
    system_id: uuid.UUID | None = Query(None),
    assignee_id: uuid.UUID | None = Query(None),
    search: str | None = Query(None),
    detected_start: datetime | None = Query(None),
    detected_end: datetime | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
) -> IncidentListResponse:
    service = IncidentService(session)
    items, total = await service.list_incidents(
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
    pages = (total + size - 1) // size
    return IncidentListResponse(
        items=[IncidentDetailResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get(
    "/{id}",
    response_model=IncidentDetailResponse,
    dependencies=[Depends(require_permissions(PermissionKey.INCIDENTS_READ))],
)
async def get_incident(
    id: Annotated[uuid.UUID, Path(...)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> IncidentDetailResponse:
    service = IncidentService(session)
    incident = await service.get_incident(id)
    return IncidentDetailResponse.model_validate(incident)


@router.put(
    "/{id}",
    response_model=IncidentDetailResponse,
    dependencies=[Depends(require_permissions(PermissionKey.INCIDENTS_UPDATE))],
)
async def update_incident(
    id: Annotated[uuid.UUID, Path(...)],
    payload: IncidentUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> IncidentDetailResponse:
    service = IncidentService(session)
    incident = await service.update_incident(id, payload, current_user.id)
    return IncidentDetailResponse.model_validate(incident)


@router.delete(
    "/{id}",
    status_code=204,
    dependencies=[Depends(require_permissions(PermissionKey.INCIDENTS_CLOSE))],
)
async def delete_incident(
    id: Annotated[uuid.UUID, Path(...)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    service = IncidentService(session)
    await service.delete_incident(id, current_user.id)


@router.post(
    "/{id}/assign",
    response_model=IncidentDetailResponse,
    dependencies=[Depends(require_permissions(PermissionKey.INCIDENTS_ASSIGN))],
)
async def assign_incident(
    id: Annotated[uuid.UUID, Path(...)],
    payload: IncidentAssign,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> IncidentDetailResponse:
    service = IncidentService(session)
    incident = await service.assign_incident(id, payload.assignee_id, current_user.id)
    return IncidentDetailResponse.model_validate(incident)


@router.post(
    "/{id}/status",
    response_model=IncidentDetailResponse,
)
async def transition_status(
    id: Annotated[uuid.UUID, Path(...)],
    payload: IncidentStatusTransition,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> IncidentDetailResponse:
    # RBAC logic: transition to Closed requires incidents:close, other transitions require incidents:update
    permission = PermissionKey.INCIDENTS_CLOSE if payload.status == IncidentStatus.CLOSED else PermissionKey.INCIDENTS_UPDATE
    
    # Manually check permissions since status value is dynamic
    user_permissions = {p.key for role in current_user.roles for p in role.permissions}
    if permission.value not in user_permissions:
        from app.core.exceptions import AppException
        raise AppException(
            status_code=403,
            code="insufficient_permissions",
            message="User does not have permission to perform this status transition.",
            details={"missing_permissions": [permission.value]},
        )
        
    service = IncidentService(session)
    incident = await service.transition_status(id, payload.status, payload.message, current_user.id)
    return IncidentDetailResponse.model_validate(incident)


@router.get(
    "/{id}/timeline",
    response_model=list[IncidentEventResponse],
    dependencies=[Depends(require_permissions(PermissionKey.INCIDENTS_READ))],
)
async def get_incident_timeline(
    id: Annotated[uuid.UUID, Path(...)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[IncidentEventResponse]:
    service = IncidentService(session)
    events = await service.get_incident_timeline(id)
    return [IncidentEventResponse.model_validate(event) for event in events]
