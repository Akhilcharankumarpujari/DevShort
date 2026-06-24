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
        for p in (permissions or ["loki:read"])
    ]
    user.roles = [role]
    return user


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_search_logs_endpoint(mock_get: MagicMock) -> None:
    client = TestClient(app)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "status": "success",
        "data": {
            "resultType": "streams",
            "result": [
                {
                    "stream": {"namespace": "default", "pod": "api-pod"},
                    "values": [
                        ["1719264000000000000", "ERROR: Connection timeout to DB"],
                        ["1719264060000000000", "Warning: Disk high usage threshold exceeded"],
                        ["1719264120000000000", "System started successfully"],
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
        response = client.get("/api/v1/logs/search?query=Connection&severity=error")
        assert response.status_code == 200
        data = response.json()
        assert "Connection" in data["query"]
        assert len(data["entries"]) == 3
        # System started -> info (newest)
        assert data["entries"][0]["severity"] == "info"
        # Warning -> warning
        assert data["entries"][1]["severity"] == "warning"
        # ERROR -> error (oldest)
        assert data["entries"][2]["severity"] == "error"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_get_pod_logs_endpoint(mock_get: MagicMock) -> None:
    client = TestClient(app)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "status": "success",
        "data": {
            "resultType": "streams",
            "result": [
                {
                    "stream": {"namespace": "default", "pod": "web-pod"},
                    "values": [["1719264000000000000", "GET /api/v1/health HTTP/1.1 200"]],
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
        response = client.get("/api/v1/logs/pods/web-pod?namespace=default&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["pod"] == "web-pod"
        assert data[0]["message"] == "GET /api/v1/health HTTP/1.1 200"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_get_namespace_logs_endpoint(mock_get: MagicMock) -> None:
    client = TestClient(app)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "status": "success",
        "data": {
            "resultType": "streams",
            "result": [
                {
                    "stream": {"namespace": "kube-system", "pod": "dns-pod"},
                    "values": [["1719264000000000000", "DNS server ready"]],
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
        response = client.get("/api/v1/logs/namespaces/kube-system?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["namespace"] == "kube-system"
        assert data[0]["message"] == "DNS server ready"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
@patch("app.services.loki_service.LokiService.stream_live_logs")
async def test_live_logs_streaming_endpoint(mock_stream: MagicMock) -> None:
    client = TestClient(app)

    from typing import Any
    from collections.abc import AsyncIterator

    async def mock_generator(*args: Any, **kwargs: Any) -> AsyncIterator[str]:
        yield "data: {\"timestamp\": \"2026-06-24T18:00:00Z\", \"message\": \"live heartbeat tick\", \"pod\": \"live-pod\", \"namespace\": \"default\"}\n\n"

    mock_stream.return_value = mock_generator()

    mock_session = AsyncMock()
    mock_user = get_mock_user()

    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        response = client.get("/api/v1/logs/live?namespace=default&query=heartbeat")
        assert response.status_code == 200
        assert "live heartbeat tick" in response.text
    finally:
        app.dependency_overrides.clear()



@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_get_log_analytics_endpoint(mock_get: MagicMock) -> None:
    client = TestClient(app)

    # Mock responses for error count, warning count, top pods, top namespaces instant queries
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "status": "success",
        "data": {
            "resultType": "vector",
            "result": [
                {
                    "metric": {"pod": "broken-pod", "namespace": "dev"},
                    "value": [1719264000, "15"],
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
        response = client.get("/api/v1/logs/analytics?duration=2h")
        assert response.status_code == 200
        data = response.json()
        assert data["error_count"] == 15
        assert data["warning_count"] == 15
        assert data["top_failing_pods"]["broken-pod"] == 15
        assert data["top_failing_namespaces"]["dev"] == 15
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_loki_connection_error(mock_get: MagicMock) -> None:
    client = TestClient(app)

    # Simulate connection refused exception
    mock_get.side_effect = httpx.ConnectError("Connection refused")

    mock_session = AsyncMock()
    mock_user = get_mock_user()

    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        response = client.get("/api/v1/logs/search?query=error")
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "loki_connection_error"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_unauthorized_loki_raises_403() -> None:
    client = TestClient(app)

    mock_session = AsyncMock()
    # Mock user with NO loki:read permission
    mock_user = get_mock_user(role_name="Viewer", permissions=["incidents:read"])

    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        response = client.get("/api/v1/logs/analytics")
        assert response.status_code == 403
        assert response.json()["error"]["code"] == "insufficient_permissions"
    finally:
        app.dependency_overrides.clear()
