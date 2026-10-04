"""Unit tests for FastAPI gateway endpoints: /health, /ready, /api/state."""
from fastapi.testclient import TestClient
import pytest
from server import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "uptime_seconds" in data
    assert "timestamp" in data


def test_ready_endpoint(client):
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert "ready" in data
    assert "worker_alive" in data
    assert "detector_ready" in data
    assert data["detector_ready"] is True


def test_api_state_endpoint(client):
    response = client.get("/api/state")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
