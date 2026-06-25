from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.rca_engine import RCAEngine
from app.api.deps import get_current_active_user, require_permissions
from app.core.config import get_settings
from app.db.session import get_db_session
from app.models.analysis import Analysis
from app.models.user import User
from app.schemas.ai import (
    AnalyzeAlertRequest,
    AnalyzeIncidentRequest,
    AnalyzePodRequest,
    AnalysisHistoryResponse,
    AnalysisResultResponse,
)
from app.security.rbac import PermissionKey

router = APIRouter()


def _map_analysis(analysis: Analysis) -> AnalysisResultResponse:
    """Convert an Analysis ORM object to the response schema."""
    evidence: dict[str, Any] = analysis.evidence or {}
    recs = analysis.recommendations or []
    token_usage_raw: dict[str, Any] = analysis.token_usage or {}

    # Recommendations can be stored as {"action": "..."} dicts or plain strings
    remediation: list[str] = []
    related: list[str] = []
    severity: str | None = str(evidence["severity"]) if "severity" in evidence else None
    impact: str | None = analysis.summary

    from app.schemas.ai import TokenUsage
    token_usage = TokenUsage(
        prompt_tokens=int(float(str(token_usage_raw.get("prompt_tokens", 0)))),
        completion_tokens=int(float(str(token_usage_raw.get("completion_tokens", 0)))),
        total_tokens=int(float(str(token_usage_raw.get("total_tokens", 0)))),
    )

    return AnalysisResultResponse(
        id=analysis.id,
        incident_id=analysis.incident_id,
        analysis_type=analysis.analysis_type,
        provider=analysis.provider or "",
        model=analysis.model or "",
        status=analysis.status,
        root_cause=analysis.root_cause or "",
        confidence_score=float(analysis.confidence_score or 0),
        severity=severity,
        impact=impact,
        recommendations=recs,
        remediation_steps=remediation,
        related_components=related,
        token_usage=token_usage,
        started_at=analysis.started_at,
        completed_at=analysis.completed_at,
        created_at=analysis.created_at,
    )


@router.post(
    "/analyze/incident",
    response_model=AnalysisResultResponse,
    status_code=200,
    summary="Run RCA on an incident",
    dependencies=[Depends(require_permissions(PermissionKey.AI_ANALYZE))],
)
async def analyze_incident(
    payload: AnalyzeIncidentRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AnalysisResultResponse:
    """Trigger AI Root Cause Analysis for a specific incident."""
    settings = get_settings()
    engine = RCAEngine(session=session, settings=settings)
    analysis = await engine.analyze_incident(
        incident_id=payload.incident_id,
        creator_id=current_user.id,
    )
    return _map_analysis(analysis)


@router.post(
    "/analyze/alert",
    response_model=AnalysisResultResponse,
    status_code=200,
    summary="Run RCA on an alert",
    dependencies=[Depends(require_permissions(PermissionKey.AI_ANALYZE))],
)
async def analyze_alert(
    payload: AnalyzeAlertRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AnalysisResultResponse:
    """Trigger AI Root Cause Analysis for a specific alert."""
    settings = get_settings()
    engine = RCAEngine(session=session, settings=settings)
    analysis = await engine.analyze_alert(
        alert_id=payload.alert_id,
        creator_id=current_user.id,
    )
    return _map_analysis(analysis)


@router.post(
    "/analyze/pod",
    response_model=AnalysisResultResponse,
    status_code=200,
    summary="Run RCA on a Kubernetes pod",
    dependencies=[Depends(require_permissions(PermissionKey.AI_ANALYZE))],
)
async def analyze_pod(
    payload: AnalyzePodRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AnalysisResultResponse:
    """Trigger AI Root Cause Analysis for a named Kubernetes pod."""
    settings = get_settings()
    engine = RCAEngine(session=session, settings=settings)
    analysis = await engine.analyze_pod(
        pod_name=payload.pod_name,
        namespace=payload.namespace,
        creator_id=current_user.id,
    )
    return _map_analysis(analysis)


@router.get(
    "/history",
    response_model=AnalysisHistoryResponse,
    summary="List all RCA analyses",
    dependencies=[Depends(require_permissions(PermissionKey.AI_READ))],
)
async def list_analyses(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    incident_id: uuid.UUID | None = Query(None),
    provider: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
) -> AnalysisHistoryResponse:
    """Return paginated list of all AI analyses, optionally filtered by incident or provider."""
    stmt = select(Analysis).where(Analysis.deleted_at.is_(None))
    if incident_id is not None:
        stmt = stmt.where(Analysis.incident_id == incident_id)
    if provider is not None:
        stmt = stmt.where(Analysis.provider == provider)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_res = await session.execute(count_stmt)
    total = total_res.scalar_one()

    stmt = stmt.order_by(Analysis.created_at.desc()).offset((page - 1) * size).limit(size)
    items_res = await session.execute(stmt)
    items = list(items_res.scalars().all())

    return AnalysisHistoryResponse(total=total, items=[_map_analysis(a) for a in items])


@router.get(
    "/history/{analysis_id}",
    response_model=AnalysisResultResponse,
    summary="Get a specific AI analysis",
    dependencies=[Depends(require_permissions(PermissionKey.AI_READ))],
)
async def get_analysis(
    analysis_id: Annotated[uuid.UUID, Path(...)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AnalysisResultResponse:
    """Retrieve a single AI analysis by its UUID."""
    stmt = select(Analysis).where(Analysis.id == analysis_id, Analysis.deleted_at.is_(None))
    res = await session.execute(stmt)
    analysis = res.scalars().first()
    if analysis is None:
        from app.core.exceptions import AppException
        raise AppException(status_code=404, code="analysis_not_found", message=f"Analysis '{analysis_id}' not found.")
    return _map_analysis(analysis)
