"""Unit tests for PID Camera Controller."""
from fastapi.testclient import TestClient
from tools.pid_controller.api import app, service


def test_pid_health():
    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["data"]["service"] == "pid_controller"


def test_pid_control_law_and_antiwindup():
    service.reset()
    # Desired center is (320, 240)
    # Target is offset at (370, 290) -> error_x = +50, error_y = +50
    out1 = service.compute(target_pos=(370.0, 290.0), dt=0.0333)

    assert out1.error_x == 50.0
    assert out1.error_y == 50.0
    assert out1.pan_speed_deg > 0.0  # Must steer right
    assert out1.tilt_speed_deg > 0.0  # Must steer down
    assert out1.pan_speed_deg <= service.config.max_pan_speed_deg

    # Run for 100 iterations with persistent error to test anti-windup clamp
    for _ in range(100):
        out_saturated = service.compute(target_pos=(500.0, 400.0), dt=0.0333)

    assert abs(out_saturated.integral_x) <= service.config.anti_windup_limit
    assert abs(out_saturated.integral_y) <= service.config.anti_windup_limit


def test_pid_deadband():
    service.reset()
    # Target is almost exactly centered: (320.2, 240.1) -> error < 0.5px deadband
    out = service.compute(target_pos=(320.2, 240.1), dt=0.0333)
    assert out.in_deadband is True
    assert out.pan_speed_deg == 0.0
    assert out.tilt_speed_deg == 0.0


def test_pid_api():
    client = TestClient(app)
    req = {"target_pos": [350.0, 260.0], "dt": 0.0333}
    res = client.post("/compute", json=req)
    assert res.status_code == 200
    data = res.json()["data"]
    assert "pan_speed_deg" in data
    assert "tilt_speed_deg" in data
    assert data["total_error_px"] > 0.0
