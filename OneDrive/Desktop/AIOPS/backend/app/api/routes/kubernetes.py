from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permissions
from app.db.session import get_db_session
from app.agents.kubernetes_agent import KubernetesAgent
from app.models.user import User
from app.security.rbac import PermissionKey
from app.schemas.kubernetes import (
    ClusterHealthResponse,
    DeploymentResponse,
    DeploymentScalePayload,
    DeploymentRollbackPayload,
    DeploymentStatusResponse,
    NamespaceResponse,
    PodDetailResponse,
    PodEventResponse,
    PodResponse,
)
from app.services.kubernetes_service import KubernetesService

router = APIRouter()

# Single agent instance shared across calls
_k8s_agent = KubernetesAgent()


def get_k8s_agent() -> KubernetesAgent:
    return _k8s_agent


def get_k8s_service(
    agent: KubernetesAgent = Depends(get_k8s_agent),
    session: AsyncSession = Depends(get_db_session),
) -> KubernetesService:
    return KubernetesService(agent, session)


@router.get("/namespaces", response_model=list[NamespaceResponse])
async def list_namespaces(
    service: KubernetesService = Depends(get_k8s_service),
    _: User = Depends(require_permissions(PermissionKey.KUBERNETES_READ)),
) -> list[NamespaceResponse]:
    return await service.list_namespaces()


@router.get("/pods", response_model=list[PodResponse])
async def list_pods(
    namespace: str | None = Query(None, description="Namespace to filter pods"),
    service: KubernetesService = Depends(get_k8s_service),
    _: User = Depends(require_permissions(PermissionKey.KUBERNETES_READ)),
) -> list[PodResponse]:
    return await service.list_pods(namespace)


@router.get("/pods/{pod_name}", response_model=PodDetailResponse)
async def get_pod_details(
    pod_name: str,
    namespace: str = Query("default", description="Namespace of the pod"),
    service: KubernetesService = Depends(get_k8s_service),
    _: User = Depends(require_permissions(PermissionKey.KUBERNETES_READ)),
) -> PodDetailResponse:
    return await service.get_pod_details(pod_name, namespace)


@router.get("/pods/{pod_name}/logs", response_model=str)
async def get_pod_logs(
    pod_name: str,
    namespace: str = Query("default", description="Namespace of the pod"),
    container: str | None = Query(None, description="Specific container name"),
    tail_lines: int | None = Query(None, description="Number of lines to show from the end"),
    service: KubernetesService = Depends(get_k8s_service),
    _: User = Depends(require_permissions(PermissionKey.KUBERNETES_READ)),
) -> str:
    return await service.get_pod_logs(pod_name, namespace, container, tail_lines)


@router.get("/pods/{pod_name}/events", response_model=list[PodEventResponse])
async def get_pod_events(
    pod_name: str,
    namespace: str = Query("default", description="Namespace of the pod"),
    service: KubernetesService = Depends(get_k8s_service),
    _: User = Depends(require_permissions(PermissionKey.KUBERNETES_READ)),
) -> list[PodEventResponse]:
    return await service.get_pod_events(pod_name, namespace)


@router.get("/deployments", response_model=list[DeploymentResponse])
async def list_deployments(
    namespace: str | None = Query(None, description="Namespace to filter deployments"),
    service: KubernetesService = Depends(get_k8s_service),
    _: User = Depends(require_permissions(PermissionKey.KUBERNETES_READ)),
) -> list[DeploymentResponse]:
    return await service.list_deployments(namespace)


@router.get("/deployments/{name}", response_model=DeploymentStatusResponse)
async def get_deployment_status(
    name: str,
    namespace: str = Query("default", description="Namespace of the deployment"),
    service: KubernetesService = Depends(get_k8s_service),
    _: User = Depends(require_permissions(PermissionKey.KUBERNETES_READ)),
) -> DeploymentStatusResponse:
    return await service.get_deployment_status(name, namespace)


@router.post("/deployments/{name}/restart", response_model=DeploymentResponse)
async def restart_deployment(
    name: str,
    namespace: str = Query("default", description="Namespace of the deployment"),
    service: KubernetesService = Depends(get_k8s_service),
    current_user: User = Depends(require_permissions(PermissionKey.KUBERNETES_WRITE)),
) -> DeploymentResponse:
    return await service.restart_deployment(name, namespace, actor_id=current_user.id)


@router.post("/deployments/{name}/scale", response_model=DeploymentResponse)
async def scale_deployment(
    name: str,
    payload: DeploymentScalePayload,
    namespace: str = Query("default", description="Namespace of the deployment"),
    service: KubernetesService = Depends(get_k8s_service),
    current_user: User = Depends(require_permissions(PermissionKey.KUBERNETES_WRITE)),
) -> DeploymentResponse:
    return await service.scale_deployment(
        name, namespace, replicas=payload.replicas, actor_id=current_user.id
    )


@router.post("/deployments/{name}/rollback", response_model=DeploymentResponse)
async def rollback_deployment(
    name: str,
    payload: DeploymentRollbackPayload,
    namespace: str = Query("default", description="Namespace of the deployment"),
    service: KubernetesService = Depends(get_k8s_service),
    current_user: User = Depends(require_permissions(PermissionKey.KUBERNETES_WRITE)),
) -> DeploymentResponse:
    return await service.rollback_deployment(
        name, namespace, revision=payload.revision, actor_id=current_user.id
    )


@router.get("/cluster/health", response_model=ClusterHealthResponse)
async def get_cluster_health(
    service: KubernetesService = Depends(get_k8s_service),
    _: User = Depends(require_permissions(PermissionKey.KUBERNETES_READ)),
) -> ClusterHealthResponse:
    return await service.get_cluster_health()
