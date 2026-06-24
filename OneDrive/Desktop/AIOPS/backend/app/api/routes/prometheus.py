from __future__ import annotations

import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permissions
from app.db.session import get_db_session
from app.core.config import get_settings
from app.models.user import User
from app.security.rbac import PermissionKey
from app.schemas.prometheus import (
    ClusterMetricsResponse,
    HistoricalMetricsResponse,
    NamespaceMetricsResponse,
    NodeMetricsResponse,
    PodMetricsResponse,
)
from app.services.prometheus_service import PrometheusService

router = APIRouter()


def get_prometheus_service(
    session: AsyncSession = Depends(get_db_session),
) -> PrometheusService:
    settings = get_settings()
    return PrometheusService(settings.prometheus_url, session)


@router.get("/cluster", response_model=ClusterMetricsResponse)
async def get_cluster_metrics(
    service: PrometheusService = Depends(get_prometheus_service),
    _: User = Depends(require_permissions(PermissionKey.PROMETHEUS_READ)),
) -> ClusterMetricsResponse:
    return await service.get_cluster_metrics()


@router.get("/nodes", response_model=list[NodeMetricsResponse])
async def get_nodes_metrics(
    service: PrometheusService = Depends(get_prometheus_service),
    _: User = Depends(require_permissions(PermissionKey.PROMETHEUS_READ)),
) -> list[NodeMetricsResponse]:
    return await service.get_nodes_metrics()


@router.get("/pods", response_model=list[PodMetricsResponse])
async def get_pods_metrics(
    namespace: str | None = Query(None, description="Filter pods by namespace"),
    service: PrometheusService = Depends(get_prometheus_service),
    _: User = Depends(require_permissions(PermissionKey.PROMETHEUS_READ)),
) -> list[PodMetricsResponse]:
    return await service.get_pods_metrics(namespace)


@router.get("/pods/{pod_name}", response_model=PodMetricsResponse)
async def get_pod_metrics(
    pod_name: str,
    namespace: str = Query("default", description="Namespace of the pod"),
    service: PrometheusService = Depends(get_prometheus_service),
    _: User = Depends(require_permissions(PermissionKey.PROMETHEUS_READ)),
) -> PodMetricsResponse:
    return await service.get_pod_metrics(pod_name, namespace)


@router.get("/namespaces/{namespace}", response_model=NamespaceMetricsResponse)
async def get_namespace_metrics(
    namespace: str,
    service: PrometheusService = Depends(get_prometheus_service),
    _: User = Depends(require_permissions(PermissionKey.PROMETHEUS_READ)),
) -> NamespaceMetricsResponse:
    return await service.get_namespace_metrics(namespace)


@router.get("/history", response_model=HistoricalMetricsResponse)
async def get_historical_metrics(
    query: str = Query(..., description="PromQL query expression"),
    start: datetime = Query(..., description="Start timestamp"),
    end: datetime = Query(..., description="End timestamp"),
    step: int = Query(60, description="Step size in seconds"),
    save_snapshot: bool = Query(False, description="Save snapshot in metrics_snapshots table"),
    incident_id: uuid.UUID | None = Query(None, description="Link snapshot to incident"),
    system_id: uuid.UUID | None = Query(None, description="Link snapshot to system"),
    summary: str | None = Query(None, description="Optional snapshot description"),
    service: PrometheusService = Depends(get_prometheus_service),
    _: User = Depends(require_permissions(PermissionKey.PROMETHEUS_READ)),
) -> HistoricalMetricsResponse:
    return await service.get_historical_metrics(
        query=query,
        start=start,
        end=end,
        step=step,
        save_snapshot=save_snapshot,
        incident_id=incident_id,
        system_id=system_id,
        summary=summary,
    )
