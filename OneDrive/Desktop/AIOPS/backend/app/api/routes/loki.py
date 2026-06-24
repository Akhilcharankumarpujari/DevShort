from __future__ import annotations

from datetime import datetime
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.api.deps import require_permissions
from app.core.config import get_settings
from app.models.user import User
from app.security.rbac import PermissionKey
from app.schemas.loki import LogAnalyticsResponse, LogEntry, LogSearchResponse
from app.services.loki_service import LokiService

router = APIRouter()


def get_loki_service() -> LokiService:
    settings = get_settings()
    return LokiService(settings.loki_url)


@router.get("/search", response_model=LogSearchResponse)
async def search_logs(
    query: str | None = Query(None, description="Search text query filter"),
    namespace: str | None = Query(None, description="Filter by namespace"),
    pod: str | None = Query(None, description="Filter by pod"),
    deployment: str | None = Query(None, description="Filter by deployment"),
    severity: str | None = Query(None, description="Filter by severity"),
    start: datetime | None = Query(None, description="Start timestamp"),
    end: datetime | None = Query(None, description="End timestamp"),
    limit: int = Query(100, ge=1, le=1000, description="Max logs limit"),
    service: LokiService = Depends(get_loki_service),
    _: User = Depends(require_permissions(PermissionKey.LOKI_READ)),
) -> LogSearchResponse:
    built_query = service._build_logql(namespace, pod, deployment, severity, query)
    entries = await service.search_logs(
        query=query,
        namespace=namespace,
        pod=pod,
        deployment=deployment,
        severity=severity,
        start=start,
        end=end,
        limit=limit,
    )
    return LogSearchResponse(query=built_query, entries=entries)


@router.get("/pods/{pod_name}", response_model=list[LogEntry])
async def get_pod_logs(
    pod_name: str,
    namespace: str = Query("default", description="Namespace of the pod"),
    limit: int = Query(100, ge=1, le=1000, description="Max logs limit"),
    service: LokiService = Depends(get_loki_service),
    _: User = Depends(require_permissions(PermissionKey.LOKI_READ)),
) -> list[LogEntry]:
    return await service.search_logs(pod=pod_name, namespace=namespace, limit=limit)


@router.get("/namespaces/{namespace}", response_model=list[LogEntry])
async def get_namespace_logs(
    namespace: str,
    limit: int = Query(100, ge=1, le=1000, description="Max logs limit"),
    service: LokiService = Depends(get_loki_service),
    _: User = Depends(require_permissions(PermissionKey.LOKI_READ)),
) -> list[LogEntry]:
    return await service.search_logs(namespace=namespace, limit=limit)


@router.get("/live")
async def stream_live_logs(
    query: str | None = Query(None, description="Search query filter"),
    namespace: str | None = Query(None, description="Filter by namespace"),
    pod: str | None = Query(None, description="Filter by pod"),
    service: LokiService = Depends(get_loki_service),
    _: User = Depends(require_permissions(PermissionKey.LOKI_READ)),
) -> StreamingResponse:
    # Streams live logs as text/event-stream (SSE)
    return StreamingResponse(
        service.stream_live_logs(query=query, namespace=namespace, pod=pod),
        media_type="text/event-stream",
    )


@router.get("/analytics", response_model=LogAnalyticsResponse)
async def get_log_analytics(
    duration: str = Query("1h", description="Duration multiplier e.g. 1h, 30m"),
    service: LokiService = Depends(get_loki_service),
    _: User = Depends(require_permissions(PermissionKey.LOKI_READ)),
) -> LogAnalyticsResponse:
    return await service.get_log_analytics(duration)


@router.get("/history", response_model=list[LogEntry])
async def get_historical_logs(
    namespace: str | None = Query(None, description="Filter by namespace"),
    pod: str | None = Query(None, description="Filter by pod"),
    start: datetime | None = Query(None, description="Start time range"),
    end: datetime | None = Query(None, description="End time range"),
    limit: int = Query(100, ge=1, le=1000, description="Max logs limit"),
    service: LokiService = Depends(get_loki_service),
    _: User = Depends(require_permissions(PermissionKey.LOKI_READ)),
) -> list[LogEntry]:
    return await service.search_logs(
        namespace=namespace, pod=pod, start=start, end=end, limit=limit
    )
