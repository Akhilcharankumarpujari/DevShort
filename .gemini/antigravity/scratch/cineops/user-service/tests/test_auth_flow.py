import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app

# Use an isolated SQLite database for integration tests
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
    yield
    app.dependency_overrides.pop(get_db, None)

client = TestClient(app)

def test_full_auth_lifecycle():
    # 1. Register User
    reg_payload = {
        "email": "testuser@cineops.com",
        "password": "mypassword123",
        "first_name": "Test",
        "last_name": "User"
    }
    register_response = client.post("/api/v1/users/register", json=reg_payload)
    assert register_response.status_code == 201
    user_data = register_response.json()
    assert user_data["email"] == reg_payload["email"]
    assert user_data["role"] == "USER"
    assert "id" in user_data

    # Register duplicate email should fail
    duplicate_res = client.post("/api/v1/users/register", json=reg_payload)
    assert duplicate_res.status_code == 400

    # 2. Login
    login_payload = {
        "email": "testuser@cineops.com",
        "password": "mypassword123"
    }
    login_response = client.post("/api/v1/users/login", json=login_payload)
    assert login_response.status_code == 200
    tokens = login_response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    # Login with wrong password should fail
    wrong_login = {"email": "testuser@cineops.com", "password": "wrongpassword"}
    wrong_res = client.post("/api/v1/users/login", json=wrong_login)
    assert wrong_res.status_code == 401

    # 3. Access Protected Route (GET /me)
    headers = {"Authorization": f"Bearer {access_token}"}
    me_response = client.get("/api/v1/users/me", headers=headers)
    assert me_response.status_code == 200
    profile = me_response.json()
    assert profile["email"] == "testuser@cineops.com"
    assert profile["first_name"] == "Test"

    # Access without token should fail
    unauth_response = client.get("/api/v1/users/me")
    assert unauth_response.status_code == 401

    # 4. Update Profile
    update_payload = {"first_name": "UpdatedName"}
    update_res = client.put("/api/v1/users/me", json=update_payload, headers=headers)
    assert update_res.status_code == 200
    updated_profile = update_res.json()
    assert updated_profile["first_name"] == "UpdatedName"
    assert updated_profile["last_name"] == "User"

    # 5. Change Password
    change_payload = {
        "old_password": "mypassword123",
        "new_password": "newsecurepassword123"
    }
    change_res = client.post("/api/v1/users/me/change-password", json=change_payload, headers=headers)
    assert change_res.status_code == 200

    # Old password login should fail now
    fail_login = client.post("/api/v1/users/login", json=login_payload)
    assert fail_login.status_code == 401

    # New password login should pass
    new_login_payload = {
        "email": "testuser@cineops.com",
        "password": "newsecurepassword123"
    }
    new_login_res = client.post("/api/v1/users/login", json=new_login_payload)
    assert new_login_res.status_code == 200
    new_tokens = new_login_res.json()
    
    # 6. Refresh Token
    refresh_payload = {"refresh_token": refresh_token}
    refresh_res = client.post("/api/v1/users/refresh", json=refresh_payload)
    assert refresh_res.status_code == 200
    refreshed_tokens = refresh_res.json()
    assert "access_token" in refreshed_tokens
    
    # 7. Logout
    logout_payload = {"refresh_token": refreshed_tokens["refresh_token"]}
    logout_res = client.post("/api/v1/users/logout", json=logout_payload)
    assert logout_res.status_code == 200

    # Using the logged out refresh token again should fail
    fail_refresh = client.post("/api/v1/users/refresh", json=logout_payload)
    assert fail_refresh.status_code == 401


def test_rbac_restrictions():
    # 1. Register Admin User
    admin_reg = {
        "email": "admin@cineops.com",
        "password": "adminpassword123",
        "role": "ADMIN"
    }
    client.post("/api/v1/users/register", json=admin_reg)
    admin_login_res = client.post("/api/v1/users/login", json={"email": "admin@cineops.com", "password": "adminpassword123"})
    admin_token = admin_login_res.json()["access_token"]

    # 2. Register Normal User
    user_reg = {
        "email": "regular@cineops.com",
        "password": "userpassword123",
        "role": "USER"
    }
    client.post("/api/v1/users/register", json=user_reg)
    user_login_res = client.post("/api/v1/users/login", json={"email": "regular@cineops.com", "password": "userpassword123"})
    user_token = user_login_res.json()["access_token"]

    # Define a temporary dummy endpoint protected by get_current_admin_user to test RBAC
    from app.utils.auth import get_current_admin_user

    @app.get("/api/v1/test-admin-only")
    def admin_only(admin: dict = Depends(get_current_admin_user)):
        return {"authorized": True}

    # Admin access should pass
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    admin_res = client.get("/api/v1/test-admin-only", headers=admin_headers)
    assert admin_res.status_code == 200
    assert admin_res.json() == {"authorized": True}

    # Regular user access should be forbidden (403)
    user_headers = {"Authorization": f"Bearer {user_token}"}
    user_res = client.get("/api/v1/test-admin-only", headers=user_headers)
    assert user_res.status_code == 403
