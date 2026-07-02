import pytest
import jwt
from datetime import date, datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app

# In-memory database for testing
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
    
    # We bypass automatic seeding for integration tests to have a predictable empty DB state.
    # We will manually seed what we need in the test setup.
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
    
    # Temporarily remove startup event so database doesn't auto-seed
    # during integration tests
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


def test_rbac_security():
    # Attempting to access admin movies without a token should fail (401)
    res = client.post("/api/v1/admin/movies", json={})
    assert res.status_code == 401

    # Accessing with normal user token should be forbidden (403)
    user_headers = get_user_headers()
    res = client.post("/api/v1/admin/movies", json={}, headers=user_headers)
    assert res.status_code == 403


def test_movie_service_integration():
    admin_headers = get_admin_headers()
    
    # 1. Create a Movie
    movie_payload = {
        "title": "Interstellar",
        "description": "Exploration of space",
        "genre": "Sci-Fi",
        "language": "English",
        "duration_minutes": 169,
        "release_date": "2014-11-07",
        "rating": 8.6,
        "status": "NOW_SHOWING"
    }
    res_movie = client.post("/api/v1/admin/movies", json=movie_payload, headers=admin_headers)
    assert res_movie.status_code == 201
    movie_id = res_movie.json()["id"]

    # 2. Create a Theatre
    theatre_payload = {
        "name": "PVR Superplex",
        "city": "Bangalore",
        "address": "Koramangala"
    }
    res_theatre = client.post("/api/v1/admin/theatres", json=theatre_payload, headers=admin_headers)
    assert res_theatre.status_code == 201
    theatre_id = res_theatre.json()["id"]

    # 3. Create a Screen
    screen_payload = {
        "theatre_id": theatre_id,
        "screen_name": "Screen 1",
        "total_seats": 200
    }
    res_screen = client.post("/api/v1/admin/screens", json=screen_payload, headers=admin_headers)
    assert res_screen.status_code == 201
    screen_id = res_screen.json()["id"]

    # 4. Create a Show
    show_start = datetime.now() + timedelta(days=1)
    show_end = show_start + timedelta(hours=3)
    show_payload = {
        "movie_id": movie_id,
        "screen_id": screen_id,
        "show_date": str(show_start.date()),
        "start_time": show_start.isoformat(),
        "end_time": show_end.isoformat(),
        "ticket_price": 250.0,
        "available_seats": 200
    }
    res_show = client.post("/api/v1/admin/shows", json=show_payload, headers=admin_headers)
    assert res_show.status_code == 201
    show_id = res_show.json()["id"]

    # 5. Overlapping Show Conflict Check
    # Attempting to schedule a show on the same screen at the same time should fail
    overlap_payload = {
        "movie_id": movie_id,
        "screen_id": screen_id,
        "show_date": str(show_start.date()),
        "start_time": (show_start + timedelta(minutes=30)).isoformat(),
        "end_time": (show_end - timedelta(minutes=30)).isoformat(),
        "ticket_price": 200.0,
        "available_seats": 200
    }
    res_overlap = client.post("/api/v1/admin/shows", json=overlap_payload, headers=admin_headers)
    assert res_overlap.status_code == 400
    assert "Schedule conflict" in res_overlap.json()["detail"]

    # 6. Exceeded Seats Capacity Check
    invalid_seats_payload = {
        "movie_id": movie_id,
        "screen_id": screen_id,
        "show_date": str(show_start.date()),
        "start_time": (show_start + timedelta(hours=4)).isoformat(),
        "end_time": (show_end + timedelta(hours=4)).isoformat(),
        "ticket_price": 200.0,
        "available_seats": 300  # Screen capacity is only 200
    }
    res_seats = client.post("/api/v1/admin/shows", json=invalid_seats_payload, headers=admin_headers)
    assert res_seats.status_code == 400
    assert "Available seats cannot exceed screen capacity" in res_seats.json()["detail"]

    # 7. Verify Public API Queries
    # Test movies listing & searching
    get_movies_res = client.get("/api/v1/movies?city=Bangalore")
    assert get_movies_res.status_code == 200
    assert len(get_movies_res.json()) == 1
    assert get_movies_res.json()[0]["title"] == "Interstellar"

    # Test cities listing
    cities_res = client.get("/api/v1/cities")
    assert cities_res.status_code == 200
    assert "Bangalore" in cities_res.json()

    # Test theatres listing
    theatres_res = client.get("/api/v1/theatres?city=Bangalore")
    assert theatres_res.status_code == 200
    assert len(theatres_res.json()) == 1
    assert theatres_res.json()[0]["name"] == "PVR Superplex"
