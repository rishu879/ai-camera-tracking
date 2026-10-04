"""Unit tests for Virtual Environment Simulator."""
from fastapi.testclient import TestClient
from tools.simulator.api import app, service


def test_simulator_health():
    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["data"]["service"] == "simulator"


def test_simulator_step_and_state():
    client = TestClient(app)
    # Reset
    res_reset = client.post("/reset")
    assert res_reset.status_code == 200

    # Step simulation
    res_step = client.post("/step?dt=0.0333")
    assert res_step.status_code == 200
    data = res_step.json()["data"]
    assert data["frame_index"] == 1
    assert len(data["targets"]) >= 1
    t0 = data["targets"][0]
    assert "x" in t0 and "y" in t0
    assert "vx" in t0 and "vy" in t0


def test_simulator_motion_types():
    # Test adding each motion type and verify stepping executes without error
    motions = ["straight", "circular", "figure_8", "random", "spiral", "sinusoidal"]
    service.reset()
    for m in motions:
        service.add_target(
            shape="square",
            size=(12, 12),
            motion_type=m,
            speed=30.0,
            initial_center=(1000.0, 1000.0),
        )

    assert len(service.targets) == len(motions) + 1  # 1 default + 6 new

    # Step forward 10 steps
    for _ in range(10):
        updated = service.step(0.0333)
        assert len(updated) == len(service.targets)
        for t in updated:
            assert 0 <= t.x <= service.width
            assert 0 <= t.y <= service.height


def test_canvas_rendering():
    client = TestClient(app)
    res = client.get("/canvas?format=base64")
    assert res.status_code == 200
    data = res.json()["data"]
    assert "image_base64" in data
    assert data["width"] == 2048
    assert data["height"] == 2048
