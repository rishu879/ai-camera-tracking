"""Unit tests for Configuration Manager."""
from fastapi.testclient import TestClient
from tools.configuration.api import app, service
from tools.configuration.config import SystemConfig


def test_health_check():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["service"] == "configuration_manager"


def test_get_and_update_config():
    client = TestClient(app)
    # Get config
    get_res = client.get("/config")
    assert get_res.status_code == 200
    cfg = get_res.json()["data"]
    assert "screen" in cfg
    assert "camera" in cfg

    # Update config
    patch = {"camera": {"max_pan_speed": 7.5}}
    post_res = client.post("/config", json=patch)
    assert post_res.status_code == 200
    updated = post_res.json()["data"]
    assert updated["camera"]["max_pan_speed"] == 7.5


def test_load_presets():
    client = TestClient(app)
    # List profiles
    prof_res = client.get("/config/profiles")
    assert prof_res.status_code == 200
    profiles = prof_res.json()["data"]
    assert "isro_benchmark_1" in profiles

    # Load ISRO benchmark 1
    load_res = client.post("/config/load_profile?name=isro_benchmark_1")
    assert load_res.status_code == 200
    cfg1 = load_res.json()["data"]
    assert cfg1["profile_name"] == "isro_benchmark_1"
    assert cfg1["screen"]["width"] == 2048
    assert cfg1["target"]["motion_type"] == "figure_8"


def test_reset_to_default():
    client = TestClient(app)
    res = client.post("/config/reset")
    assert res.status_code == 200
    cfg = res.json()["data"]
    assert cfg["profile_name"] == "default"
