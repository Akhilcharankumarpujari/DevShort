import pytest
import jwt
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app

# Isolated SQLite database for integration tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(autouse=True)
def override_db(db_session):
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[app.on_event("startup")] = lambda: None
    yield
    app.dependency_overrides.pop(get_db, None)

client = TestClient(app)

SECRET_KEY = "cineops-super-secure-jwt-secret-key-change-in-prod"
ALGORITHM = "HS256"

def get_admin_headers():
    payload = {
        "sub": "admin_user_id",
        "email": "admin@cineops.com",
        "role": "ADMIN",
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return {"Authorization": f"Bearer {token}"}

def get_user_headers():
    payload = {
        "sub": "user_id",
        "email": "user@cineops.com",
        "role": "USER",
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return {"Authorization": f"Bearer {token}"}


def test_notification_delivery_flow(db_session):
    user_headers = get_user_headers()

    # 1. Send successful booking confirmation
    payload = {
        "booking_reference": "CINE-FLOW-REF-1",
        "user_id": "user_id",
        "notification_type": "Booking Confirmation",
        "channel": "EMAIL",
        "subject": "Booking Confirmed!",
        "message": "Your seats have been booked."
    }
    res = client.post("/api/v1/notifications/send", json=payload, headers=user_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "SENT"
    assert data["retry_count"] == 0
    assert data["delivered_at"] is not None
    notification_id = data["id"]

    # 2. Duplicate prevention check: sending again returns the existing notification
    res_dup = client.post("/api/v1/notifications/send", json=payload, headers=user_headers)
    assert res_dup.status_code == 200
    assert res_dup.json()["id"] == notification_id

    # 3. Verify user list contains it
    res_list = client.get("/api/v1/notifications", headers=user_headers)
    assert res_list.status_code == 200
    assert len(res_list.json()) > 0

    # 4. Verify history log
    res_hist = client.get("/api/v1/notifications/history", headers=user_headers)
    assert res_hist.status_code == 200
    assert len(res_hist.json()) >= 2  # PENDING history and SENT history


def test_notification_auto_retry_flow(db_session):
    user_headers = get_user_headers()

    # Send notification containing "fail" key to trigger simulated channel error and retry loop
    payload = {
        "booking_reference": "CINE-FLOW-REF-2",
        "user_id": "user_id",
        "notification_type": "Payment Failure",
        "channel": "SMS",
        "subject": "Payment failed",
        "message": "The transaction fail error occurred."
    }
    res = client.post("/api/v1/notifications/send", json=payload, headers=user_headers)
    assert res.status_code == 201
    data = res.json()
    # Should have executed auto-retries up to 3 and transitioned to FAILED
    assert data["status"] == "FAILED"
    assert data["retry_count"] == 3


def test_admin_rbac_restrictions():
    # Attempting to fetch all logs without admin token should fail (403)
    res = client.get("/api/v1/admin/notifications", headers=get_user_headers())
    assert res.status_code == 403

    # Admin access should pass
    res_admin = client.get("/api/v1/admin/notifications", headers=get_admin_headers())
    assert res_admin.status_code == 200
