from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app
from app.database import get_db

client = TestClient(app)

def mock_get_db():
    class MockDB:
        def execute(self, query):
            class MockResult:
                pass
            return MockResult()
    db = MockDB()
    try:
        yield db
    finally:
        pass

app.dependency_overrides[get_db] = mock_get_db

@patch("app.main.httpx.AsyncClient")
def test_health(mock_httpx_client):
    # Mock the AsyncClient.get call to return status code 200
    mock_response = AsyncMock()
    mock_response.status_code = 200
    
    mock_instance = AsyncMock()
    mock_instance.get.return_value = mock_response
    mock_httpx_client.return_value.__aenter__.return_value = mock_instance

    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert data["dependencies"]["movie-service"] == "connected"

def test_metrics():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
