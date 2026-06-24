from __future__ import annotations

import uuid
from datetime import datetime, UTC
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_current_user
from app.db.session import get_db_session
from app.models.user import User, Role, Permission
from app.models.alert import Alert, AlertStatus, AlertSeverity
from app.models.incident import Incident, IncidentStatus, IncidentSeverity, IncidentPriority
from app.models.system import System
from app.schemas.alertmanager import AlertmanagerWebhook, AlertmanagerAlert
from app.services.alertmanager_service import AlertmanagerService


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
        for p in (permissions or ["alerts:read", "alerts:write"])
    ]
    user.roles = [role]
    return user


def get_mock_alert(alert_id: uuid.UUID | None = None) -> Alert:
    a_id = alert_id or uuid.uuid4()
    alert = Alert(
        id=a_id,
        source="alertmanager",
        external_id="fingerprint123",
        fingerprint="fingerprint123",
        title="HighCpuUsage",
        description="CPU high on api pod",
        severity="critical",
        status="firing",
        system_id=uuid.uuid4(),
        incident_id=uuid.uuid4(),
        starts_at=datetime.now(UTC),
        labels={"pod": "api-pod", "namespace": "default"},
        annotations={"summary": "CPU high"},
        raw_payload={},
    )
    alert.created_at = datetime.now(UTC)
    alert.updated_at = datetime.now(UTC)
    return alert


@pytest.mark.asyncio
@patch("app.services.alertmanager_service.AlertmanagerService.process_webhook")
async def test_webhook_ingestion_endpoint(mock_process: MagicMock) -> None:
    client = TestClient(app)

    mock_process.return_value = {
        "alerts_processed": 1,
        "incidents_created": 1,
        "incidents_correlated": 0,
    }

    mock_session = AsyncMock()
    mock_user = get_mock_user(role_name="SRE")

    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_current_user] = lambda: mock_user

    payload = {
        "receiver": "webhook",
        "status": "firing",
        "alerts": [
            {
                "status": "firing",
                "labels": {"alertname": "HighCpuUsage", "severity": "critical", "pod": "api-pod"},
                "annotations": {"summary": "CPU usage critical"},
                "startsAt": "2026-06-24T18:00:00Z",
                "fingerprint": "fingerprint123",
            }
        ],
        "version": "4",
    }

    try:
        response = client.post("/api/v1/alerts/webhook", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processed"
        assert data["alerts_processed"] == 1
        assert data["incidents_created"] == 1
        assert data["incidents_correlated"] == 0
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
@patch("app.services.alertmanager_service.AlertmanagerService.get_alerts")
async def test_list_alerts_endpoint(mock_get: MagicMock) -> None:
    client = TestClient(app)

    mock_alert = get_mock_alert()
    mock_get.return_value = [mock_alert]

    mock_session = AsyncMock()
    mock_user = get_mock_user()

    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        response = client.get("/api/v1/alerts?status=firing&severity=critical")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "HighCpuUsage"
        assert data[0]["severity"] == "critical"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
@patch("app.services.alertmanager_service.AlertmanagerService.get_alert_by_id")
async def test_get_alert_by_id_endpoint(mock_get: MagicMock) -> None:
    client = TestClient(app)

    alert_id = uuid.uuid4()
    mock_alert = get_mock_alert(alert_id=alert_id)
    mock_get.return_value = mock_alert

    mock_session = AsyncMock()
    mock_user = get_mock_user()

    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        response = client.get(f"/api/v1/alerts/{alert_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(alert_id)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
@patch("app.services.alertmanager_service.AlertmanagerService.get_correlated_alerts")
async def test_list_correlated_alerts_endpoint(mock_get: MagicMock) -> None:
    client = TestClient(app)

    alert_id = uuid.uuid4()
    incident_id = uuid.uuid4()
    mock_get.return_value = [
        {
            "alert_id": alert_id,
            "fingerprint": "fp123",
            "title": "HighCpu",
            "incident_id": incident_id,
            "incident_number": "INC-001",
            "incident_title": "Cpu Spike",
            "incident_status": "open",
        }
    ]

    mock_session = AsyncMock()
    mock_user = get_mock_user()

    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        response = client.get("/api/v1/alerts/incidents")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["incident_number"] == "INC-001"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
@patch("app.services.alertmanager_service.AlertmanagerService.get_alerts_history")
async def test_list_alerts_history_endpoint(mock_get: MagicMock) -> None:
    client = TestClient(app)

    mock_alert = get_mock_alert()
    mock_get.return_value = [mock_alert]

    mock_session = AsyncMock()
    mock_user = get_mock_user()

    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        response = client.get("/api/v1/alerts/history?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_unauthorized_user_raises_403() -> None:
    client = TestClient(app)

    mock_session = AsyncMock()
    mock_user = get_mock_user(role_name="Viewer", permissions=["incidents:read"])

    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        response = client.post("/api/v1/alerts/webhook", json={})
        assert response.status_code == 403

        response = client.get("/api/v1/alerts")
        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_service_escalate_severity() -> None:
    session = AsyncMock()
    session.add = MagicMock()
    service = AlertmanagerService(session)

    incident = Incident(
        id=uuid.uuid4(),
        severity="sev3",
        priority="p3",
        title="Test Incident",
        status="open",
    )

    await service._check_and_escalate_severity(incident, "critical", "AlertName")
    assert incident.severity == "sev1"
    assert incident.priority == "p1"


@pytest.mark.asyncio
async def test_service_find_system() -> None:
    session = AsyncMock()
    service = AlertmanagerService(session)

    system = System(id=uuid.uuid4(), name="payment-service", slug="payment-service")
    mock_res = MagicMock()
    mock_res.scalars.return_value.first.return_value = system
    session.execute.return_value = mock_res

    sys_id = await service._find_system({"service": "payment-service"})
    assert sys_id == system.id


@pytest.mark.asyncio
@patch("app.services.incident_service.IncidentService.create_incident")
async def test_service_process_webhook_firing(mock_create_inc: MagicMock) -> None:
    session = AsyncMock()
    session.add = MagicMock()
    service = AlertmanagerService(session)

    # Mock DB executes
    mock_res_alert = MagicMock()
    mock_res_alert.scalars().first.return_value = None  # New alert
    mock_res_inc = MagicMock()
    mock_res_inc.scalars().all.return_value = []  # No active incidents
    session.execute.side_effect = [mock_res_alert, mock_res_inc]

    incident_id = uuid.uuid4()
    incident = Incident(
        id=incident_id,
        severity="sev1",
        priority="p1",
        title="Alert Triggered",
        incident_number="INC-12345",
    )
    mock_create_inc.return_value = incident

    webhook = AlertmanagerWebhook(
        receiver="webhook",
        status="firing",
        alerts=[
            AlertmanagerAlert(
                status="firing",
                labels={"alertname": "DatabaseDeadlock", "severity": "critical", "pod": "db-pod"},
                annotations={"summary": "DB lock occurred"},
                startsAt=datetime.now(UTC),
                fingerprint="fp123",
            )
        ],
        version="4",
    )

    res = await service.process_webhook(webhook)
    assert res["alerts_processed"] == 1
    assert res["incidents_created"] == 1
    assert res["incidents_correlated"] == 0
