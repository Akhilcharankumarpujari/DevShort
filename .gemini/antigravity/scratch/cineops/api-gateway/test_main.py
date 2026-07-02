from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app

client = TestClient(app)

@patch("app.main.httpx.AsyncClient")
def test_health(mock_httpx_client):
    # Mock downstream service checks
    mock_response = AsyncMock()
    mock_response.status_code = 200
    
    mock_instance = AsyncMock()
    mock_instance.get.return_value = mock_response
    mock_httpx_client.return_value.__aenter__.return_value = mock_instance

    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "api-gateway"
    assert data["dependencies"]["users"] == "connected"

def test_metrics():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
