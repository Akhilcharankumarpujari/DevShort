from __future__ import annotations

import uuid
from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from kubernetes.client import Configuration  # type: ignore

# Disable SDK client-side validation to simplify mock object creation
config_override = Configuration.get_default_copy()
config_override.client_side_validation = False
Configuration.set_default(config_override)
from fastapi.testclient import TestClient
from kubernetes.client.exceptions import ApiException  # type: ignore

from app.main import app
from app.api.deps import get_current_user
from app.db.session import get_db_session
from app.models.user import User, Role, Permission
from app.services.kubernetes_service import KubernetesService, handle_k8s_errors
from app.core.exceptions import AppException

# Mock imports from kubernetes.client
from kubernetes.client import (
    V1Namespace,
    V1NamespaceStatus,
    V1ObjectMeta,
    V1Pod,
    V1PodSpec,
    V1PodStatus,
    V1Container,
    V1ContainerStatus,
    V1ContainerState,
    V1ContainerStateRunning,
    CoreV1Event,
    V1EventSource,
    V1Deployment,
    V1DeploymentSpec,
    V1DeploymentStatus,
    V1DeploymentCondition,
    V1ReplicaSet,
    V1ReplicaSetSpec,
    V1PodTemplateSpec,
    V1Node,
    V1NodeStatus,
    V1NodeCondition,
    V1ObjectReference,
)


def get_mock_user(role_name: str = "Developer", permissions: list[str] | None = None) -> User:
    user = User(
        id=uuid.uuid4(),
        email="test@aiops.com",
        full_name="Test User",
        status="active",
    )
    role = Role(name=role_name)
    role.permissions = [
        Permission(key=p)
        for p in (permissions or ["kubernetes:read", "kubernetes:write"])
    ]
    user.roles = [role]
    return user


@pytest.mark.asyncio
async def test_k8s_errors_handling_404() -> None:
    async def failing_func() -> None:
        raise ApiException(status=404, reason="Not Found")

    with pytest.raises(AppException) as exc_info:
        async with handle_k8s_errors():
            await failing_func()

    assert exc_info.value.status_code == 404
    assert exc_info.value.code == "k8s_resource_not_found"


@pytest.mark.asyncio
async def test_k8s_errors_handling_connection_failure() -> None:
    async def failing_func() -> None:
        raise ConnectionRefusedError("Connection refused")

    with pytest.raises(AppException) as exc_info:
        async with handle_k8s_errors():
            await failing_func()

    assert exc_info.value.status_code == 503
    assert exc_info.value.code == "k8s_connection_error"


@pytest.mark.asyncio
@patch("app.api.routes.kubernetes._k8s_agent")
async def test_list_namespaces_endpoint(mock_agent: MagicMock) -> None:
    client = TestClient(app)
    
    mock_ns = V1Namespace(
        metadata=V1ObjectMeta(name="production", creation_timestamp=datetime.now(UTC)),
        status=V1NamespaceStatus(phase="Active"),
    )
    mock_agent.list_namespaces.return_value = [mock_ns]

    mock_session = AsyncMock()
    mock_user = get_mock_user()

    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        response = client.get("/api/v1/k8s/namespaces")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "production"
        assert data[0]["status"] == "Active"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
@patch("app.api.routes.kubernetes._k8s_agent")
async def test_get_pod_details_endpoint(mock_agent: MagicMock) -> None:
    client = TestClient(app)

    mock_pod = V1Pod(
        metadata=V1ObjectMeta(
            name="api-pod",
            namespace="default",
            labels={"app": "api"},
            annotations={"prometheus.io/scrape": "true"},
            creation_timestamp=datetime.now(UTC),
        ),
        spec=V1PodSpec(
            containers=[V1Container(name="web", image="nginx:latest")],
            node_name="node-1",
        ),
        status=V1PodStatus(
            phase="Running",
            pod_ip="10.244.1.20",
            container_statuses=[
                V1ContainerStatus(
                    name="web",
                    image="nginx:latest",
                    ready=True,
                    restart_count=2,
                    state=V1ContainerState(running=V1ContainerStateRunning()),
                )
            ],
        ),
    )
    mock_agent.get_pod.return_value = mock_pod

    mock_session = AsyncMock()
    mock_user = get_mock_user()

    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        response = client.get("/api/v1/k8s/pods/api-pod?namespace=default")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "api-pod"
        assert data["status"] == "Running"
        assert data["ip"] == "10.244.1.20"
        assert len(data["containers"]) == 1
        assert data["containers"][0]["name"] == "web"
        assert data["containers"][0]["ready"] is True
        assert data["containers"][0]["restart_count"] == 2
        assert data["containers"][0]["state"] == "Running"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
@patch("app.api.routes.kubernetes._k8s_agent")
async def test_get_pod_logs_endpoint(mock_agent: MagicMock) -> None:
    client = TestClient(app)

    mock_agent.get_pod_logs.return_value = "Starting service...\nListening on port 8080"

    mock_session = AsyncMock()
    mock_user = get_mock_user()

    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        response = client.get("/api/v1/k8s/pods/api-pod/logs?namespace=default&tail_lines=10")
        assert response.status_code == 200
        assert response.json() == "Starting service...\nListening on port 8080"
        mock_agent.get_pod_logs.assert_called_once_with("api-pod", "default", None, 10)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
@patch("app.api.routes.kubernetes._k8s_agent")
async def test_get_pod_events_endpoint(mock_agent: MagicMock) -> None:
    client = TestClient(app)

    mock_event = CoreV1Event(
        type="Warning",
        reason="FailedScheduling",
        message="0/1 nodes are available: 1 Insufficient cpu.",
        source=V1EventSource(component="default-scheduler"),
        count=3,
        first_timestamp=datetime.now(UTC),
        last_timestamp=datetime.now(UTC),
        metadata=V1ObjectMeta(name="event-1"),
    )
    mock_agent.get_pod_events.return_value = [mock_event]

    mock_session = AsyncMock()
    mock_user = get_mock_user()

    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        response = client.get("/api/v1/k8s/pods/api-pod/events?namespace=default")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["type"] == "Warning"
        assert data[0]["reason"] == "FailedScheduling"
        assert "Insufficient cpu" in data[0]["message"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
@patch("app.api.routes.kubernetes._k8s_agent")
async def test_scale_deployment_endpoint(mock_agent: MagicMock) -> None:
    client = TestClient(app)

    mock_dep = V1Deployment(
        metadata=V1ObjectMeta(name="frontend", namespace="default", creation_timestamp=datetime.now(UTC)),
        spec=V1DeploymentSpec(replicas=5, selector=None, template=None),
        status=V1DeploymentStatus(replicas=5, available_replicas=5, ready_replicas=5, updated_replicas=5),
    )
    mock_agent.scale_deployment.return_value = mock_dep

    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_user = get_mock_user()

    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        response = client.post(
            "/api/v1/k8s/deployments/frontend/scale?namespace=default",
            json={"replicas": 5},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "frontend"
        assert data["replicas"] == 5

        # Verify audit logs were written to the session
        mock_session.add.assert_called_once()
        audit_log = mock_session.add.call_args[0][0]
        assert audit_log.action == "k8s:deployment:scale"
        assert audit_log.resource_id == "default/frontend"
        assert audit_log.outcome == "success"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
@patch("app.api.routes.kubernetes._k8s_agent")
async def test_rollback_deployment_endpoint(mock_agent: MagicMock) -> None:
    client = TestClient(app)

    mock_dep = V1Deployment(
        metadata=V1ObjectMeta(name="frontend", namespace="default", creation_timestamp=datetime.now(UTC)),
        spec=V1DeploymentSpec(replicas=3, selector=None, template=None),
        status=V1DeploymentStatus(replicas=3, available_replicas=3, ready_replicas=3, updated_replicas=3),
    )
    mock_agent.rollback_deployment.return_value = (mock_dep, 2)

    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_user = get_mock_user()

    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        response = client.post(
            "/api/v1/k8s/deployments/frontend/rollback?namespace=default",
            json={"revision": 2},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "frontend"

        # Verify audit logs were written to the session
        mock_session.add.assert_called_once()
        audit_log = mock_session.add.call_args[0][0]
        assert audit_log.action == "k8s:deployment:rollback"
        assert audit_log.resource_id == "default/frontend"
        assert audit_log.outcome == "success"
        assert audit_log.details["applied_revision"] == 2
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
@patch("app.api.routes.kubernetes._k8s_agent")
async def test_cluster_health_endpoint(mock_agent: MagicMock) -> None:
    client = TestClient(app)

    mock_node = V1Node(
        metadata=V1ObjectMeta(name="node-1"),
        status=V1NodeStatus(
            conditions=[V1NodeCondition(type="Ready", status="True")]
        ),
    )
    mock_pod = V1Pod(
        metadata=V1ObjectMeta(name="pod-1"),
        status=V1PodStatus(phase="Running"),
    )
    mock_ns = V1Namespace(
        metadata=V1ObjectMeta(name="default"),
        status=V1NamespaceStatus(phase="Active"),
    )

    mock_agent.list_nodes.return_value = [mock_node]
    mock_agent.list_pods.return_value = [mock_pod]
    mock_agent.list_namespaces.return_value = [mock_ns]

    mock_session = AsyncMock()
    mock_user = get_mock_user()

    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        response = client.get("/api/v1/k8s/cluster/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["nodes"]["total"] == 1
        assert data["nodes"]["ready"] == 1
        assert data["pods"]["total"] == 1
        assert data["pods"]["running"] == 1
        assert "default" in data["namespaces"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_unauthorized_endpoints_raises_403() -> None:
    client = TestClient(app)

    mock_session = AsyncMock()
    # Mock user with NO k8s permissions
    mock_user = get_mock_user(role_name="Viewer", permissions=["incidents:read"])

    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        response = client.get("/api/v1/k8s/namespaces")
        assert response.status_code == 403
        assert response.json()["error"]["code"] == "insufficient_permissions"
    finally:
        app.dependency_overrides.clear()
