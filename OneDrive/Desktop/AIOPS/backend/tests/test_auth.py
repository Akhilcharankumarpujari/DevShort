import pytest
import asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from app.main import app
from app.db.session import AsyncSessionLocal, dispose_engine
from app.models.user import User, RefreshToken, user_roles

@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
async def cleanup_db():
    async with AsyncSessionLocal() as session:
        await session.execute(delete(user_roles))
        await session.execute(delete(RefreshToken))
        await session.execute(delete(User))
        await session.commit()
    yield

@pytest.mark.asyncio
async def test_register_first_user_as_admin() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "admin@example.com",
                "full_name": "Admin User",
                "password": "Password123!"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["user"]["email"] == "admin@example.com"
        assert "Admin" in [role["name"] for role in data["user"]["roles"]]
        assert "tokens" in data
        assert "access_token" in data["tokens"]
        assert "refresh_token" in data["tokens"]

@pytest.mark.asyncio
async def test_register_subsequent_user_as_viewer() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Register first user (Admin)
        response1 = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "admin@example.com",
                "full_name": "Admin User",
                "password": "Password123!"
            }
        )
        assert response1.status_code == 201

        # Register second user (Viewer)
        response2 = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "viewer@example.com",
                "full_name": "Viewer User",
                "password": "Password123!"
            }
        )
        assert response2.status_code == 201
        data = response2.json()
        assert data["user"]["email"] == "viewer@example.com"
        assert "Viewer" in [role["name"] for role in data["user"]["roles"]]

@pytest.mark.asyncio
async def test_register_duplicate_email_returns_409() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Register first user
        response1 = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@example.com",
                "full_name": "Test User",
                "password": "Password123!"
            }
        )
        assert response1.status_code == 201

        # Register again with same email
        response2 = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@example.com",
                "full_name": "Test User",
                "password": "Password123!"
            }
        )
        assert response2.status_code == 409
        assert response2.json()["error"]["code"] == "email_already_registered"

@pytest.mark.asyncio
async def test_login_successful() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Register user
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "login@example.com",
                "full_name": "Login User",
                "password": "Password123!"
            }
        )

        # Login
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "login@example.com",
                "password": "Password123!"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "tokens" in data
        assert "access_token" in data["tokens"]
