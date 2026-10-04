"""Unit tests for Virtual Camera service."""
import numpy as np
from fastapi.testclient import TestClient
from tools.virtual_camera.api import app, service


def test_virtual_camera_health():
    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["data"]["service"] == "virtual_camera"


def test_virtual_camera_ptz_speed_clamp():
    client = TestClient(app)
    # Command speed beyond 5 deg/s limit
    res = client.post("/ptz/speed", json={"pan_speed_deg": 12.0, "tilt_speed_deg": -15.0})
    assert res.status_code == 200
    state = res.json()["data"]
    # Verify clamped to max_pan_speed_deg (default 5.0)
    assert abs(state["pan_speed_cmd"]) <= 5.0
    assert abs(state["tilt_speed_cmd"]) <= 5.0


def test_virtual_camera_step_integration():
    service.reset()
    service.set_ptz_speed(2.0, 1.0)
    canvas = np.zeros((2048, 2048), dtype=np.uint8)
    canvas[1020:1030, 1020:1030] = 255

    # Step forward 1.0 second (30 frames at dt=1/30)
    for _ in range(30):
        frame = service.step(1.0 / 30.0, canvas)
        assert frame.shape == (480, 640)

    state = service.get_state()
    # Pan should be approx 2.0 deg, tilt approx 1.0 deg
    assert abs(state["pan_deg"] - 2.0) < 0.1
    assert abs(state["tilt_deg"] - 1.0) < 0.1


def test_virtual_camera_frame_api():
    client = TestClient(app)
    res = client.get("/frame?format=base64")
    assert res.status_code == 200
    data = res.json()["data"]
    assert "image_base64" in data
    assert data["width"] == 640
    assert data["height"] == 480
