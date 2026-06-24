from __future__ import annotations

import uuid
from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import httpx
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_current_user
from app.db.session import get_db_session
from app.models.user import User, Role, Permission
from app.services.prometheus_service import MemoryCache, PrometheusService
from app.core.exceptions import AppException


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
        for p in (permissions or ["prometheus:read"])
    ]
    user.roles = [role]
    return user


@pytest.fixture(autouse=True)
def clear_prometheus_cache() -> None:
    from app.services.prometheus_service import _metrics_cache
    _metrics_cache.clear()


def test_cache_hits_and_misses() -> None:
    cache = MemoryCache(default_ttl_seconds=1)
    
    # Cache miss
    assert cache.get("key1") is None
    
    # Cache hit
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"
    
    # Expiration (sleep or wait)
    import time
    time.sleep(1.1)
    assert cache.get("key1") is None


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_get_nodes_metrics_endpoint(mock_get: MagicMock) -> None:
    client = TestClient(app)

    # Mock responses for CPU, memory, disk, network rx, network tx queries
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "status": "success",
        "data": {
            "resultType": "vector",
            "result": [
                {
                    "metric": {"instance": "node-1:9100"},
                    "value": [1719264000, "15.5"],
                }
            ],
        },
    }
    mock_get.return_value = mock_resp

    mock_session = AsyncMock()
    mock_user = get_mock_user()

    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        response = client.get("/api/v1/metrics/nodes")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["node_name"] == "node-1"
        assert data[0]["cpu_usage_pct"] == 15.5
        assert data[0]["memory_usage_pct"] == 15.5
        assert data[0]["disk_usage_pct"] == 15.5
        assert data[0]["network_rx_bytes_sec"] == 15.5
        assert data[0]["network_tx_bytes_sec"] == 15.5
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_get_pods_metrics_endpoint(mock_get: MagicMock) -> None:
    client = TestClient(app)

    # Mock responses for CPU, memory, restarts, status
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "status": "success",
        "data": {
            "resultType": "vector",
            "result": [
                {
                    "metric": {"pod": "api-pod", "namespace": "default", "status": "Running"},
                    "value": [1719264000, "2.5"],
                }
            ],
        },
    }
    mock_get.return_value = mock_resp

    mock_session = AsyncMock()
    mock_user = get_mock_user()

    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        response = client.get("/api/v1/metrics/pods?namespace=default")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["pod_name"] == "api-pod"
        assert data[0]["namespace"] == "default"
        assert data[0]["cpu_cores"] == 2.5
        assert data[0]["memory_bytes"] == 2
        assert data[0]["restarts"] == 2
        assert data[0]["status"] == "Running"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_get_cluster_metrics_endpoint(mock_get: MagicMock) -> None:
    client = TestClient(app)

    # Mock responses for nodes, nodes_ready, pods, pods_running, pods_failed, namespaces_pods
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "status": "success",
        "data": {
            "resultType": "vector",
            "result": [
                {
                    "metric": {"namespace": "default"},
                    "value": [1719264000, "10"],
                }
            ],
        },
    }
    mock_get.return_value = mock_resp

    mock_session = AsyncMock()
    mock_user = get_mock_user()

    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        response = client.get("/api/v1/metrics/cluster")
        assert response.status_code == 200
        data = response.json()
        assert data["nodes_total"] == 10
        assert data["nodes_ready"] == 10
        assert data["pods_total"] == 10
        assert data["pods_running"] == 10
        assert data["pods_failed"] == 10
        assert len(data["namespaces"]) == 1
        assert data["namespaces"][0]["namespace"] == "default"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_get_historical_metrics_no_snapshot(mock_get: MagicMock) -> None:
    client = TestClient(app)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "status": "success",
        "data": {
            "resultType": "matrix",
            "result": [
                {
                    "metric": {"pod": "api-pod"},
                    "values": [
                        [1719264000, "0.15"],
                        [1719264060, "0.18"],
                    ],
                }
            ],
        },
    }
    mock_get.return_value = mock_resp

    mock_session = AsyncMock()
    mock_user = get_mock_user()

    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        url = "/api/v1/metrics/history?query=up&start=2026-06-24T23:00:00Z&end=2026-06-24T23:05:00Z&step=60"
        response = client.get(url)
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "up"
        assert len(data["series"]) == 1
        assert data["series"][0]["metric_labels"]["pod"] == "api-pod"
        assert len(data["series"][0]["samples"]) == 2
        assert data["series"][0]["samples"][0]["value"] == 0.15
        assert data["snapshot_id"] is None
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_get_historical_metrics_with_snapshot(mock_get: MagicMock) -> None:
    client = TestClient(app)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "status": "success",
        "data": {
            "resultType": "matrix",
            "result": [
                {
                    "metric": {"pod": "api-pod"},
                    "values": [
                        [1719264000, "0.15"],
                        [1719264060, "0.18"],
                    ],
                }
            ],
        },
    }
    mock_get.return_value = mock_resp

    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_user = get_mock_user()

    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        url = (
            "/api/v1/metrics/history?query=up&start=2026-06-24T23:00:00Z&end=2026-06-24T23:05:00Z"
            "&step=60&save_snapshot=true&summary=SRE Snapshot"
        )
        response = client.get(url)
        assert response.status_code == 200
        data = response.json()
        assert data["snapshot_id"] is not None

        # Verify record added to the DB session
        mock_session.add.assert_called_once()
        snapshot = mock_session.add.call_args[0][0]
        assert snapshot.query == "up"
        assert snapshot.summary == "SRE Snapshot"
        assert snapshot.statistics["min"] == 0.15
        assert snapshot.statistics["max"] == 0.18
        assert snapshot.statistics["avg"] == pytest.approx(0.165)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_prometheus_connection_refused(mock_get: MagicMock) -> None:
    client = TestClient(app)

    # Simulate httpx exception
    mock_get.side_effect = httpx.ConnectError("Connection refused")

    mock_session = AsyncMock()
    mock_user = get_mock_user()

    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        response = client.get("/api/v1/metrics/nodes")
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "prometheus_connection_error"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_unauthorized_metrics_raises_403() -> None:
    client = TestClient(app)

    mock_session = AsyncMock()
    # Mock user with NO prometheus:read permission
    mock_user = get_mock_user(role_name="Viewer", permissions=["incidents:read"])

    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        response = client.get("/api/v1/metrics/cluster")
        assert response.status_code == 403
        assert response.json()["error"]["code"] == "insufficient_permissions"
    finally:
        app.dependency_overrides.clear()
