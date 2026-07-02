from fastapi.testclient import TestClient
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

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"

def test_metrics():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
