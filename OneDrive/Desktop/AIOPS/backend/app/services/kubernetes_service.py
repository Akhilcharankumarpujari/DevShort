from __future__ import annotations

import asyncio
import contextlib
import logging
import uuid
from collections.abc import AsyncIterator
from typing import Any, cast

from kubernetes.client.exceptions import ApiException
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.kubernetes_agent import KubernetesAgent
from app.core.exceptions import AppException
from app.models.audit import AuditActorType, AuditLog, AuditOutcome
from app.schemas.kubernetes import (
    ClusterHealthResponse,
    ContainerStatus,
    DeploymentCondition,
    DeploymentResponse,
    DeploymentStatusResponse,
    NamespaceResponse,
    NodeSummary,
    PodDetailResponse,
    PodEventResponse,
    PodResponse,
    PodSummary,
)

logger = logging.getLogger(__name__)


@contextlib.asynccontextmanager
async def handle_k8s_errors() -> AsyncIterator[None]:
    try:
        yield
    except ApiException as e:
        logger.warning("Kubernetes API error: status=%s, reason=%s", e.status, e.reason)
        if e.status == 404:
            raise AppException(
                status_code=404,
                code="k8s_resource_not_found",
                message="The requested Kubernetes resource was not found.",
            ) from e
        elif e.status == 403:
            raise AppException(
                status_code=403,
                code="k8s_forbidden",
                message="Forbidden access to the Kubernetes resource.",
            ) from e
        elif e.status == 401:
            raise AppException(
                status_code=401,
                code="k8s_unauthorized",
                message="Unauthorized access to the Kubernetes API.",
            ) from e
        else:
            raise AppException(
                status_code=500,
                code="k8s_api_error",
                message=f"Kubernetes API error: {e.reason or 'unknown error'}",
            ) from e
    except Exception as e:
        logger.exception("Unexpected error in Kubernetes Service")
        raise AppException(
            status_code=503,
            code="k8s_connection_error",
            message="Failed to connect to the Kubernetes cluster.",
        ) from e


class KubernetesService:
    def __init__(self, agent: KubernetesAgent, session: AsyncSession) -> None:
        self.agent = agent
        self.session = session

    async def _log_audit_event(
        self,
        *,
        actor_id: uuid.UUID | None,
        action: str,
        resource_id: str,
        outcome: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        audit = AuditLog(
            actor_id=actor_id,
            actor_type=AuditActorType.USER.value if actor_id else AuditActorType.SYSTEM.value,
            action=action,
            resource_type="kubernetes_deployment",
            resource_id=resource_id,
            outcome=outcome,
            details=details or {},
        )
        self.session.add(audit)

    async def list_namespaces(self) -> list[NamespaceResponse]:
        async with handle_k8s_errors():
            raw_ns = await asyncio.to_thread(self.agent.list_namespaces)
            return [
                NamespaceResponse(
                    name=ns.metadata.name or "unknown",
                    status=ns.status.phase or "Unknown",
                    created_at=ns.metadata.creation_timestamp,
                )
                for ns in raw_ns
            ]

    async def list_pods(self, namespace: str | None = None) -> list[PodResponse]:
        async with handle_k8s_errors():
            raw_pods = await asyncio.to_thread(self.agent.list_pods, namespace)
            return [
                PodResponse(
                    name=pod.metadata.name or "unknown",
                    namespace=pod.metadata.namespace or "default",
                    status=pod.status.phase or "Unknown",
                    ip=pod.status.pod_ip,
                    node_name=pod.spec.node_name,
                    created_at=pod.metadata.creation_timestamp,
                )
                for pod in raw_pods
            ]

    async def get_pod_details(self, name: str, namespace: str) -> PodDetailResponse:
        async with handle_k8s_errors():
            pod = await asyncio.to_thread(self.agent.get_pod, name, namespace)
            
            containers = []
            status_map = {}
            if pod.status and pod.status.container_statuses:
                for cs in pod.status.container_statuses:
                    state_str = "Unknown"
                    if cs.state:
                        if cs.state.running:
                            state_str = "Running"
                        elif cs.state.terminated:
                            state_str = f"Terminated (Exit Code {cs.state.terminated.exit_code})"
                        elif cs.state.waiting:
                            state_str = f"Waiting ({cs.state.waiting.reason})"
                    status_map[cs.name] = {
                        "ready": bool(cs.ready),
                        "restart_count": int(cs.restart_count or 0),
                        "state": state_str,
                    }

            if pod.spec and pod.spec.containers:
                for c in pod.spec.containers:
                    c_status = status_map.get(
                        c.name, {"ready": False, "restart_count": 0, "state": "Waiting"}
                    )
                    containers.append(
                        ContainerStatus(
                            name=c.name or "unknown",
                            image=c.image or "unknown",
                            ready=cast(bool, c_status["ready"]),
                            restart_count=cast(int, c_status["restart_count"]),
                            state=cast(str, c_status["state"]),
                        )
                    )

            return PodDetailResponse(
                name=pod.metadata.name or "unknown",
                namespace=pod.metadata.namespace or "default",
                status=pod.status.phase or "Unknown",
                ip=pod.status.pod_ip,
                node_name=pod.spec.node_name,
                created_at=pod.metadata.creation_timestamp,
                labels=pod.metadata.labels or {},
                annotations=pod.metadata.annotations or {},
                containers=containers,
            )

    async def get_pod_logs(
        self,
        name: str,
        namespace: str,
        container: str | None = None,
        tail_lines: int | None = None,
    ) -> str:
        async with handle_k8s_errors():
            return await asyncio.to_thread(
                self.agent.get_pod_logs, name, namespace, container, tail_lines
            )

    async def get_pod_events(self, name: str, namespace: str) -> list[PodEventResponse]:
        async with handle_k8s_errors():
            raw_events = await asyncio.to_thread(self.agent.get_pod_events, name, namespace)
            return [
                PodEventResponse(
                    type=evt.type or "Normal",
                    reason=evt.reason or "Unknown",
                    message=evt.message or "",
                    source=evt.source.component or evt.source.host or "unknown",
                    count=evt.count,
                    first_timestamp=evt.first_timestamp or evt.event_time,
                    last_timestamp=evt.last_timestamp or evt.event_time,
                )
                for evt in raw_events
            ]

    async def list_deployments(self, namespace: str | None = None) -> list[DeploymentResponse]:
        async with handle_k8s_errors():
            raw_deps = await asyncio.to_thread(self.agent.list_deployments, namespace)
            return [
                DeploymentResponse(
                    name=dep.metadata.name or "unknown",
                    namespace=dep.metadata.namespace or "default",
                    replicas=dep.spec.replicas or 0 if dep.spec else 0,
                    available_replicas=dep.status.available_replicas or 0 if dep.status else 0,
                    ready_replicas=dep.status.ready_replicas or 0 if dep.status else 0,
                    updated_replicas=dep.status.updated_replicas or 0 if dep.status else 0,
                    created_at=dep.metadata.creation_timestamp,
                )
                for dep in raw_deps
            ]

    async def get_deployment_status(self, name: str, namespace: str) -> DeploymentStatusResponse:
        async with handle_k8s_errors():
            dep = await asyncio.to_thread(self.agent.get_deployment, name, namespace)
            
            conditions = []
            if dep.status and dep.status.conditions:
                for cond in dep.status.conditions:
                    conditions.append(
                        DeploymentCondition(
                            type=cond.type,
                            status=cond.status,
                            reason=cond.reason,
                            message=cond.message,
                        )
                    )

            return DeploymentStatusResponse(
                name=dep.metadata.name or "unknown",
                namespace=dep.metadata.namespace or "default",
                replicas=dep.spec.replicas or 0 if dep.spec else 0,
                available_replicas=dep.status.available_replicas or 0 if dep.status else 0,
                ready_replicas=dep.status.ready_replicas or 0 if dep.status else 0,
                updated_replicas=dep.status.updated_replicas or 0 if dep.status else 0,
                conditions=conditions,
            )

    async def restart_deployment(
        self,
        name: str,
        namespace: str,
        actor_id: uuid.UUID,
    ) -> DeploymentResponse:
        async with handle_k8s_errors():
            try:
                dep = await asyncio.to_thread(self.agent.restart_deployment, name, namespace)
                await self._log_audit_event(
                    actor_id=actor_id,
                    action="k8s:deployment:restart",
                    resource_id=f"{namespace}/{name}",
                    outcome=AuditOutcome.SUCCESS.value,
                )
                await self.session.commit()
                return DeploymentResponse(
                    name=dep.metadata.name or "unknown",
                    namespace=dep.metadata.namespace or "default",
                    replicas=dep.spec.replicas or 0 if dep.spec else 0,
                    available_replicas=dep.status.available_replicas or 0 if dep.status else 0,
                    ready_replicas=dep.status.ready_replicas or 0 if dep.status else 0,
                    updated_replicas=dep.status.updated_replicas or 0 if dep.status else 0,
                    created_at=dep.metadata.creation_timestamp,
                )
            except Exception as e:
                await self._log_audit_event(
                    actor_id=actor_id,
                    action="k8s:deployment:restart",
                    resource_id=f"{namespace}/{name}",
                    outcome=AuditOutcome.FAILURE.value,
                    details={"error": str(e)},
                )
                await self.session.commit()
                raise

    async def scale_deployment(
        self,
        name: str,
        namespace: str,
        replicas: int,
        actor_id: uuid.UUID,
    ) -> DeploymentResponse:
        async with handle_k8s_errors():
            try:
                dep = await asyncio.to_thread(self.agent.scale_deployment, name, namespace, replicas)
                await self._log_audit_event(
                    actor_id=actor_id,
                    action="k8s:deployment:scale",
                    resource_id=f"{namespace}/{name}",
                    outcome=AuditOutcome.SUCCESS.value,
                    details={"replicas": replicas},
                )
                await self.session.commit()
                return DeploymentResponse(
                    name=dep.metadata.name or "unknown",
                    namespace=dep.metadata.namespace or "default",
                    replicas=dep.spec.replicas or 0 if dep.spec else 0,
                    available_replicas=dep.status.available_replicas or 0 if dep.status else 0,
                    ready_replicas=dep.status.ready_replicas or 0 if dep.status else 0,
                    updated_replicas=dep.status.updated_replicas or 0 if dep.status else 0,
                    created_at=dep.metadata.creation_timestamp,
                )
            except Exception as e:
                await self._log_audit_event(
                    actor_id=actor_id,
                    action="k8s:deployment:scale",
                    resource_id=f"{namespace}/{name}",
                    outcome=AuditOutcome.FAILURE.value,
                    details={"replicas": replicas, "error": str(e)},
                )
                await self.session.commit()
                raise

    async def rollback_deployment(
        self,
        name: str,
        namespace: str,
        revision: int,
        actor_id: uuid.UUID,
    ) -> DeploymentResponse:
        async with handle_k8s_errors():
            try:
                dep, actual_revision = await asyncio.to_thread(
                    self.agent.rollback_deployment, name, namespace, revision
                )
                await self._log_audit_event(
                    actor_id=actor_id,
                    action="k8s:deployment:rollback",
                    resource_id=f"{namespace}/{name}",
                    outcome=AuditOutcome.SUCCESS.value,
                    details={"target_revision": revision, "applied_revision": actual_revision},
                )
                await self.session.commit()
                return DeploymentResponse(
                    name=dep.metadata.name or "unknown",
                    namespace=dep.metadata.namespace or "default",
                    replicas=dep.spec.replicas or 0 if dep.spec else 0,
                    available_replicas=dep.status.available_replicas or 0 if dep.status else 0,
                    ready_replicas=dep.status.ready_replicas or 0 if dep.status else 0,
                    updated_replicas=dep.status.updated_replicas or 0 if dep.status else 0,
                    created_at=dep.metadata.creation_timestamp,
                )
            except Exception as e:
                await self._log_audit_event(
                    actor_id=actor_id,
                    action="k8s:deployment:rollback",
                    resource_id=f"{namespace}/{name}",
                    outcome=AuditOutcome.FAILURE.value,
                    details={"target_revision": revision, "error": str(e)},
                )
                await self.session.commit()
                raise

    async def get_cluster_health(self) -> ClusterHealthResponse:
        async with handle_k8s_errors():
            # Run fetches in parallel using asyncio.gather
            nodes_task = asyncio.to_thread(self.agent.list_nodes)
            pods_task = asyncio.to_thread(self.agent.list_pods)
            ns_task = asyncio.to_thread(self.agent.list_namespaces)
            
            raw_nodes, raw_pods, raw_ns = await asyncio.gather(
                nodes_task, pods_task, ns_task
            )

            # Node status computation
            total_nodes = len(raw_nodes)
            ready_nodes = 0
            for node in raw_nodes:
                if node.status and node.status.conditions:
                    for cond in node.status.conditions:
                        if cond.type == "Ready" and cond.status == "True":
                            ready_nodes += 1
                            break
            not_ready_nodes = total_nodes - ready_nodes

            # Pod status computation
            total_pods = len(raw_pods)
            running_pods = 0
            pending_pods = 0
            failed_pods = 0
            for pod in raw_pods:
                phase = pod.status.phase if pod.status else "Unknown"
                if phase == "Running":
                    running_pods += 1
                elif phase == "Pending":
                    pending_pods += 1
                elif phase == "Failed":
                    failed_pods += 1
            unknown_pods = total_pods - (running_pods + pending_pods + failed_pods)

            # Namespace summary
            namespaces = [ns.metadata.name or "unknown" for ns in raw_ns]

            # Overall status
            status = "healthy"
            if not_ready_nodes > 0:
                status = "degraded"
            if total_nodes == 0 or ready_nodes == 0:
                status = "unhealthy"

            return ClusterHealthResponse(
                status=status,
                nodes=NodeSummary(
                    total=total_nodes, ready=ready_nodes, not_ready=not_ready_nodes
                ),
                pods=PodSummary(
                    total=total_pods,
                    running=running_pods,
                    pending=pending_pods,
                    failed=failed_pods,
                    unknown=unknown_pods,
                ),
                namespaces=namespaces,
            )
