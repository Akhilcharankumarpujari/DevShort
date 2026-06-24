from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_liveness_root() -> None:
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_liveness_versioned() -> None:
    response = client.get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
