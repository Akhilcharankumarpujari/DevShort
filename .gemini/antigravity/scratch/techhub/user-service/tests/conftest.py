import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base_class import Base
from app.db.session import get_db
from app.core.security import hash_password

# Use an in-memory SQLite database for testing.
# StaticPool is used to share the connection between multiple threads/sessions.
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db() -> Generator:
    # Create the database tables
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Drop tables after test completes
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db) -> Generator:
    # Override get_db dependency to use the test database session
    def override_get_db():
        try:
            yield db
        finally:
            pass
            
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def admin_headers(client, db) -> dict:
    # Create an admin user directly in the test database
    from app.models.user import User
    admin = User(
        first_name="Admin",
        last_name="User",
        email="admin@techhub.com",
        phone="123456789",
        password_hash=hash_password("adminpassword"),
        role="admin",
        is_active=True
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    
    # Login to retrieve token
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@techhub.com", "password": "adminpassword"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function")
def customer_headers(client, db) -> dict:
    # Create a customer user directly in the test database
    from app.models.user import User
    customer = User(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        phone="987654321",
        password_hash=hash_password("customerpassword"),
        role="customer",
        is_active=True
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    
    # Login to retrieve token
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "john@example.com", "password": "customerpassword"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
