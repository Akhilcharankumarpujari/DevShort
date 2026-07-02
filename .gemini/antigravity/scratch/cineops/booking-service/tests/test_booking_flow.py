import pytest
import jwt
from datetime import datetime, timedelta, timezone
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

# Shared token helpers
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


@patch("app.routes.bookings.get_show_details")
@patch("app.routes.bookings.update_show_seats")
def test_booking_lifecycle_integration(mock_update_seats, mock_get_show, db_session):
    # Mock show service responses
    mock_get_show.return_value = {
        "id": "mock-show-id",
        "movie_id": "mock-movie-id",
        "screen_id": "mock-screen-id",
        "start_time": (datetime.now() + timedelta(days=1)).isoformat(),
        "available_seats": 200,
        "ticket_price": 250.0
    }
    mock_update_seats.return_value = True

    user_headers = get_user_headers()

    # 1. Lock Seats
    lock_payload = {
        "show_id": "mock-show-id",
        "movie_id": "mock-movie-id",
        "theatre_id": "mock-theatre-id",
        "screen_id": "mock-screen-id",
        "seats": [
            {"seat_number": "A1", "seat_type": "REGULAR", "seat_price": 250.0},
            {"seat_number": "A2", "seat_type": "REGULAR", "seat_price": 250.0}
        ]
    }
    res_lock = client.post("/api/v1/bookings/lock-seats", json=lock_payload, headers=user_headers)
    assert res_lock.status_code == 201
    lock_data = res_lock.json()
    assert lock_data["status"] == "PENDING"
    assert lock_data["total_amount"] == 500.0
    booking_id = lock_data["booking_id"]

    # 2. Attempt double locking (same seats) -> should fail
    res_double_lock = client.post("/api/v1/bookings/lock-seats", json=lock_payload, headers=user_headers)
    assert res_double_lock.status_code == 400
    assert "temporarily locked" in res_double_lock.json()["detail"]

    # 3. Confirm Booking
    res_confirm = client.post("/api/v1/bookings/confirm", json={"booking_id": booking_id}, headers=user_headers)
    assert res_confirm.status_code == 200
    confirm_data = res_confirm.json()
    assert confirm_data["booking_status"] == "CONFIRMED"
    assert confirm_data["payment_status"] == "SUCCESS"

    # 4. Attempt double booking (same seats after confirmation) -> should fail
    res_post_confirm_lock = client.post("/api/v1/bookings/lock-seats", json=lock_payload, headers=user_headers)
    assert res_post_confirm_lock.status_code == 400
    assert "already booked" in res_post_confirm_lock.json()["detail"]

    # 5. Retrieve bookings
    res_list = client.get("/api/v1/bookings", headers=user_headers)
    assert res_list.status_code == 200
    assert len(res_list.json()) > 0

    # 6. Retrieve history
    res_hist = client.get("/api/v1/bookings/history", headers=user_headers)
    assert res_hist.status_code == 200
    assert len(res_hist.json()) >= 2  # PENDING status and CONFIRMED status

    # 7. Cancel Booking
    res_cancel = client.post("/api/v1/bookings/cancel", json={"booking_id": booking_id}, headers=user_headers)
    assert res_cancel.status_code == 200
    assert res_cancel.json()["booking_status"] == "CANCELLED"
    assert res_cancel.json()["payment_status"] == "REFUNDED"


@patch("app.routes.bookings.get_show_details")
def test_booking_lock_expiration(mock_get_show, db_session):
    mock_get_show.return_value = {
        "id": "mock-show-id-exp",
        "movie_id": "mock-movie-id",
        "screen_id": "mock-screen-id",
        "start_time": (datetime.now() + timedelta(days=1)).isoformat(),
        "available_seats": 200,
        "ticket_price": 250.0
    }
    
    user_headers = get_user_headers()
    
    # Lock Seats
    lock_payload = {
        "show_id": "mock-show-id-exp",
        "movie_id": "mock-movie-id",
        "theatre_id": "mock-theatre-id",
        "screen_id": "mock-screen-id",
        "seats": [
            {"seat_number": "B1", "seat_type": "REGULAR", "seat_price": 250.0}
        ]
    }
    res_lock = client.post("/api/v1/bookings/lock-seats", json=lock_payload, headers=user_headers)
    booking_id = res_lock.json()["booking_id"]

    # Mock time to exceed lock threshold (6 minutes in future)
    future_time = datetime.utcnow() + timedelta(minutes=6)
    with patch("app.routes.bookings.datetime") as mock_datetime:
        mock_datetime.utcnow.return_value = future_time
        mock_datetime.fromisoformat = datetime.fromisoformat
        mock_datetime.now.return_value = datetime.now()
        
        # Confirm should now fail because locks expired
        res_confirm = client.post("/api/v1/bookings/confirm", json={"booking_id": booking_id}, headers=user_headers)
        assert res_confirm.status_code == 400
        assert "expired" in res_confirm.json()["detail"].lower()


def test_admin_rbac_restrictions():
    # Attempting to fetch all bookings without admin token should fail (403 or 401)
    res = client.get("/api/v1/admin/bookings", headers=get_user_headers())
    assert res.status_code == 403

    # Admin access should pass
    res_admin = client.get("/api/v1/admin/bookings", headers=get_admin_headers())
    assert res_admin.status_code == 200
