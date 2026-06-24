from __future__ import annotations

import uuid
from datetime import datetime, UTC
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.exceptions import AppException
from app.api.deps import get_current_user
from app.db.session import get_db_session
from app.models.incident import Incident, IncidentStatus, IncidentSeverity, IncidentPriority
from app.models.user import User, Role, Permission
from app.schemas.incident import IncidentCreate, IncidentUpdate
from app.services.incident_service import IncidentService

# Mock user with developer role for dependency override
def get_mock_user(role_name: str = "Developer", permissions: list[str] | None = None) -> User:
    user = User(
        id=uuid.uuid4(),
        email="test@aiops.com",
        full_name="Test User",
        status="active",
    )
    role = Role(name=role_name)
    role.permissions = [Permission(key=p) for p in (permissions or ["incidents:read", "incidents:create", "incidents:update"])]
    user.roles = [role]
    return user


def test_status_transition_validation() -> None:
    session = AsyncMock()
    service = IncidentService(session)
    
    # Valid transitions
    service._validate_status_transition(IncidentStatus.OPEN, IncidentStatus.INVESTIGATING)
    service._validate_status_transition(IncidentStatus.INVESTIGATING, IncidentStatus.RESOLVED)
    service._validate_status_transition(IncidentStatus.RESOLVED, IncidentStatus.CLOSED)
    service._validate_status_transition(IncidentStatus.CLOSED, IncidentStatus.OPEN)

    # Invalid transitions
    with pytest.raises(AppException) as exc_info:
        service._validate_status_transition(IncidentStatus.CLOSED, IncidentStatus.RESOLVED)
    assert exc_info.value.code == "invalid_status_transition"


@pytest.mark.asyncio
async def test_create_incident_generates_correct_details() -> None:
    session = AsyncMock()
    session.add = MagicMock()
    # Mock return value for count query
    session.scalar.return_value = 0 
    
    service = IncidentService(session)
    
    payload = IncidentCreate(
        title="Database Latency Spike",
        description="High read latency on primary replica.",
        severity=IncidentSeverity.SEV1,
        priority=IncidentPriority.P1,
        system_id=uuid.uuid4(),
        labels={"service": "postgres"},
    )
    
    actor_id = uuid.uuid4()
    
    # Mock repo.create to return the incident
    cast(Any, service.repo).create = AsyncMock()
    cast(Any, service.repo).add_event = AsyncMock()
    cast(Any, service.repo).get_by_id = AsyncMock()
    
    await service.create_incident(payload, actor_id)
    
    # Verify that the session add was called and sequential incident number was generated
    cast(Any, service.repo.create).assert_called_once()
    incident = cast(Any, service.repo.create).call_args[0][0]
    
    assert incident.title == "Database Latency Spike"
    assert incident.status == "open"
    assert incident.source == "manual"
    assert incident.incident_number.startswith(f"INC-{datetime.now(UTC).strftime('%Y%m%d')}-")
    
    # Verify events and audits were logged
    cast(Any, service.repo.add_event).assert_called_once()
    event = cast(Any, service.repo.add_event).call_args[0][0]
    assert event.event_type == "incident_created"
    assert event.actor_id == actor_id


def test_list_incidents_api_endpoint() -> None:
    client = TestClient(app)
    
    # Mock database session and mock query results
    mock_session = AsyncMock()
    mock_user = get_mock_user()
    
    incident = Incident(
        id=uuid.uuid4(),
        incident_number="INC-20260624-0001",
        title="Test Incident",
        severity="sev3",
        priority="p3",
        status="open",
        detected_at=datetime.now(UTC),
        labels={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    
    # Mock repository method output
    mock_execute = MagicMock()
    mock_execute.scalars.return_value.all.return_value = [incident]
    mock_session.execute.return_value = mock_execute
    mock_session.scalar.return_value = 1  # Total count

    # Apply overrides
    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    try:
        response = client.get("/api/v1/incidents/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["title"] == "Test Incident"
        assert data["items"][0]["incident_number"] == "INC-20260624-0001"
    finally:
        app.dependency_overrides.clear()


def test_insufficient_permissions_raises_403() -> None:
    client = TestClient(app)
    
    mock_session = AsyncMock()
    # Mock user with ONLY read permissions (Viewer role)
    mock_user = get_mock_user(role_name="Viewer", permissions=["incidents:read"])
    
    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    try:
        payload = {
            "title": "Unauthorized Incident Creation",
            "severity": "sev3",
            "priority": "p3"
        }
        # Post request requires incidents:create permission
        response = client.post("/api/v1/incidents/", json=payload)
        assert response.status_code == 403
        assert response.json()["error"]["code"] == "insufficient_permissions"
    finally:
        app.dependency_overrides.clear()
