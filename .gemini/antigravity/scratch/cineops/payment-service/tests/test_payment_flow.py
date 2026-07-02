import pytest
import jwt
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
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


@patch("app.routes.payments.get_booking_details")
@patch("app.routes.payments.confirm_booking")
@patch("app.routes.payments.cancel_booking")
def test_payment_lifecycle_integration(mock_cancel, mock_confirm, mock_get_booking, db_session):
    # Mock booking service responses
    mock_get_booking.return_value = {
        "id": "mock-booking-id-flow",
        "booking_reference": "CINE-20260630-ABCDEF",
        "booking_status": "PENDING",
        "total_amount": 500.0
    }
    mock_confirm.return_value = True
    mock_cancel.return_value = True

    user_headers = get_user_headers()

    # 1. Create Payment Intent
    create_payload = {
        "booking_id": "mock-booking-id-flow",
        "booking_reference": "CINE-20260630-ABCDEF",
        "amount": 500.0,
        "currency": "INR",
        "payment_method": "CARD"
    }
    res_create = client.post("/api/v1/payments/create", json=create_payload, headers=user_headers)
    assert res_create.status_code == 201
    payment_data = res_create.json()
    assert payment_data["payment_status"] == "PENDING"
    payment_id = payment_data["id"]

    # 2. Idempotency Check: creating again returns existing payment
    res_dup = client.post("/api/v1/payments/create", json=create_payload, headers=user_headers)
    assert res_dup.status_code == 200
    assert res_dup.json()["id"] == payment_id

    # 3. Confirm Payment
    res_confirm = client.post("/api/v1/payments/confirm", json={"payment_id": payment_id}, headers=user_headers)
    assert res_confirm.status_code == 200
    confirm_data = res_confirm.json()
    assert confirm_data["payment_status"] == "SUCCESS"
    assert confirm_data["transaction_id"] is not None
    mock_confirm.assert_called_with("mock-booking-id-flow", "user_id")

    # 4. Refund Payment
    refund_payload = {
        "payment_id": payment_id,
        "refund_amount": 500.0,
        "refund_reason": "Customer cancelled"
    }
    res_refund = client.post("/api/v1/payments/refund", json=refund_payload, headers=user_headers)
    assert res_refund.status_code == 200
    refund_data = res_refund.json()
    assert refund_data["refund_status"] == "SUCCESS"
    assert refund_data["refund_amount"] == 500.0
    mock_cancel.assert_called_with("mock-booking-id-flow", "user_id")


@patch("app.routes.payments.get_booking_details")
@patch("app.routes.payments.cancel_booking")
def test_payment_failure_flow(mock_cancel, mock_get_booking, db_session):
    mock_get_booking.return_value = {
        "id": "mock-booking-id-fail",
        "booking_reference": "CINE-FAIL-REF",
        "booking_status": "PENDING",
        "total_amount": 350.0
    }
    mock_cancel.return_value = True

    user_headers = get_user_headers()

    # Create Payment Intent
    create_payload = {
        "booking_id": "mock-booking-id-fail",
        "booking_reference": "CINE-FAIL-REF",
        "amount": 350.0
    }
    res_create = client.post("/api/v1/payments/create", json=create_payload, headers=user_headers)
    payment_id = res_create.json()["id"]

    # Fail Payment
    res_fail = client.post("/api/v1/payments/fail", json={"payment_id": payment_id}, headers=user_headers)
    assert res_fail.status_code == 200
    fail_data = res_fail.json()
    assert fail_data["payment_status"] == "FAILED"
    mock_cancel.assert_called_with("mock-booking-id-fail", "user_id")


def test_admin_rbac_restrictions():
    # Attempting to fetch all payments without admin token should fail (403)
    res = client.get("/api/v1/admin/payments", headers=get_user_headers())
    assert res.status_code == 403

    # Admin access should pass
    res_admin = client.get("/api/v1/admin/payments", headers=get_admin_headers())
    assert res_admin.status_code == 200
