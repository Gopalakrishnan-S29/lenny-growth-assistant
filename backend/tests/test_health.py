
from fastapi.testclient import TestClient

from app.main import app


def test_root_endpoint():
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.json()["docs"] == "/docs"


def test_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "ok"
    assert data["application"] == "The Lenny Growth Assistant"


def test_readiness_endpoint_handles_missing_ollama():
    with TestClient(app) as client:
        response = client.get("/api/health/ready")

    assert response.status_code == 200
    assert response.json()["dependencies"]["ollama"] in {
        "available",
        "unavailable",
    }
