from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.jenkins_agent import JenkinsAgent
from app.api.deps import get_current_active_user, require_permissions
from app.core.config import get_settings
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.jenkins import (
    JenkinsAnalyzeResponse,
    JenkinsBuildDetailResponse,
    JenkinsBuildListResponse,
    JenkinsCancelResponse,
    JenkinsConsoleResponse,
    JenkinsJobDetailResponse,
    JenkinsJobListResponse,
    JenkinsTriggerRequest,
    JenkinsTriggerResponse,
)
from app.security.rbac import PermissionKey
from app.services.jenkins_service import JenkinsService

router = APIRouter()


def _get_agent() -> JenkinsAgent:
    """Build a JenkinsAgent from current application settings."""
    settings = get_settings()
    return JenkinsAgent(
        base_url=settings.jenkins_url,
        username=settings.jenkins_username,
        api_token=settings.jenkins_api_token.get_secret_value() if settings.jenkins_api_token else "",
        timeout=settings.jenkins_request_timeout,
    )


# --------------------------------------------------------------------------- #
#  Jobs                                                                         #
# --------------------------------------------------------------------------- #

@router.get(
    "/jobs",
    response_model=JenkinsJobListResponse,
    summary="List all Jenkins jobs",
    dependencies=[Depends(require_permissions(PermissionKey.JENKINS_READ))],
)
async def list_jobs(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> JenkinsJobListResponse:
    """Return all top-level Jenkins jobs with their current build status color."""
    svc = JenkinsService(agent=_get_agent(), session=session)
    return await svc.list_jobs()


@router.get(
    "/jobs/{job_name}",
    response_model=JenkinsJobDetailResponse,
    summary="Get Jenkins job details",
    dependencies=[Depends(require_permissions(PermissionKey.JENKINS_READ))],
)
async def get_job(
    job_name: Annotated[str, Path(description="Jenkins job name")],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> JenkinsJobDetailResponse:
    """Return full job detail including health reports and recent builds."""
    svc = JenkinsService(agent=_get_agent(), session=session)
    return await svc.get_job(job_name)


# --------------------------------------------------------------------------- #
#  Builds                                                                       #
# --------------------------------------------------------------------------- #

@router.get(
    "/jobs/{job_name}/builds",
    response_model=JenkinsBuildListResponse,
    summary="Get build history for a job",
    dependencies=[Depends(require_permissions(PermissionKey.JENKINS_READ))],
)
async def get_build_history(
    job_name: Annotated[str, Path(description="Jenkins job name")],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    limit: int = Query(25, ge=1, le=100, description="Maximum number of builds to return"),
) -> JenkinsBuildListResponse:
    """Return paginated build history for a specific job."""
    svc = JenkinsService(agent=_get_agent(), session=session)
    return await svc.get_build_history(job_name, limit=limit)


@router.get(
    "/jobs/{job_name}/builds/{build_number}",
    response_model=JenkinsBuildDetailResponse,
    summary="Get build details",
    dependencies=[Depends(require_permissions(PermissionKey.JENKINS_READ))],
)
async def get_build(
    job_name: Annotated[str, Path(description="Jenkins job name")],
    build_number: Annotated[int, Path(ge=1, description="Build number")],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> JenkinsBuildDetailResponse:
    """Return full detail for a single build including changeset and artifacts."""
    svc = JenkinsService(agent=_get_agent(), session=session)
    return await svc.get_build(job_name, build_number)


@router.post(
    "/jobs/{job_name}/build",
    response_model=JenkinsTriggerResponse,
    status_code=201,
    summary="Trigger a new build",
    dependencies=[Depends(require_permissions(PermissionKey.JENKINS_WRITE))],
)
async def trigger_build(
    job_name: Annotated[str, Path(description="Jenkins job name")],
    payload: JenkinsTriggerRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> JenkinsTriggerResponse:
    """Queue a new Jenkins build, optionally passing build parameters."""
    svc = JenkinsService(agent=_get_agent(), session=session)
    return await svc.trigger_build(job_name, parameters=payload.parameters or None)


@router.post(
    "/jobs/{job_name}/builds/{build_number}/cancel",
    response_model=JenkinsCancelResponse,
    summary="Cancel a running build",
    dependencies=[Depends(require_permissions(PermissionKey.JENKINS_WRITE))],
)
async def cancel_build(
    job_name: Annotated[str, Path(description="Jenkins job name")],
    build_number: Annotated[int, Path(ge=1, description="Build number")],
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> JenkinsCancelResponse:
    """Stop a running Jenkins build."""
    svc = JenkinsService(agent=_get_agent(), session=session)
    return await svc.cancel_build(job_name, build_number)


@router.get(
    "/jobs/{job_name}/builds/{build_number}/logs",
    response_model=JenkinsConsoleResponse,
    summary="Download build console log",
    dependencies=[Depends(require_permissions(PermissionKey.JENKINS_READ))],
)
async def get_build_logs(
    job_name: Annotated[str, Path(description="Jenkins job name")],
    build_number: Annotated[int, Path(ge=1, description="Build number")],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> JenkinsConsoleResponse:
    """Return the full console output for a build."""
    svc = JenkinsService(agent=_get_agent(), session=session)
    return await svc.get_build_logs(job_name, build_number)


@router.post(
    "/jobs/{job_name}/builds/{build_number}/analyze",
    response_model=JenkinsAnalyzeResponse,
    summary="Run AI RCA on a build failure",
    dependencies=[Depends(require_permissions(PermissionKey.JENKINS_ANALYZE))],
)
async def analyze_build(
    job_name: Annotated[str, Path(description="Jenkins job name")],
    build_number: Annotated[int, Path(ge=1, description="Build number")],
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> JenkinsAnalyzeResponse:
    """
    Collect build logs and metadata, forward them to the AI RCA engine,
    and return a structured root cause analysis.
    """
    settings = get_settings()
    svc = JenkinsService(agent=_get_agent(), session=session)
    analysis = await svc.analyze_build(
        job_name=job_name,
        build_number=build_number,
        settings=settings,
        creator_id=current_user.id,
    )

    token_usage_raw = analysis.token_usage or {}
    evidence = analysis.evidence or {}
    recs = analysis.recommendations or []

    return JenkinsAnalyzeResponse(
        analysis_id=analysis.id,
        job_name=job_name,
        build_number=build_number,
        build_result=str(evidence.get("labels", "")).split("result': '")[-1].split("'")[0] or None,
        provider=analysis.provider or "",
        model=analysis.model or "",
        root_cause=analysis.root_cause or "",
        confidence_score=float(analysis.confidence_score or 0),
        severity=str(evidence.get("severity")) if "severity" in evidence else None,
        impact=analysis.summary,
        recommendations=recs,
        remediation_steps=[],
        related_components=[],
    )
