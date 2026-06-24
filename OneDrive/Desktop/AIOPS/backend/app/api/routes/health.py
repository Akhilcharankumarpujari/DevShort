from __future__ import annotations

from fastapi import APIRouter, Response, status

from app.core.config import get_settings
from app.db.health import check_database_health
from app.schemas.health import DependencyHealth, LivenessResponse, ReadinessResponse

router = APIRouter(tags=["health"])


@router.get("/health/live", response_model=LivenessResponse, summary="Liveness check")
async def liveness() -> LivenessResponse:
    settings = get_settings()
    return LivenessResponse(
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment.value,
    )


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Service is not ready"}},
    summary="Readiness check",
)
async def readiness(response: Response) -> ReadinessResponse:
    settings = get_settings()
    database_health = DependencyHealth(**await check_database_health())
    is_ready = database_health.status == "up"
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadinessResponse(
        status="ready" if is_ready else "not_ready",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment.value,
        dependencies={"database": database_health},
    )
