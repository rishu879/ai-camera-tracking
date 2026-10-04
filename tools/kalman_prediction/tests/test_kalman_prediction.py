"""Unit tests for Kalman Prediction Engine."""
from fastapi.testclient import TestClient
from tools.kalman_prediction.api import app, service


def test_kalman_health():
    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["data"]["service"] == "kalman_prediction"


def test_kalman_state_estimation_and_velocity():
    service.reset()
    # Feed linear trajectory moving at 10 pixels/frame in x, 5 in y
    # Frame 1 to 10
    for i in range(10):
        meas = (100.0 + i * 10.0, 50.0 + i * 5.0)
        output = service.update(meas)

    assert abs(output.position[0] - 190.0) < 3.0
    assert abs(output.position[1] - 95.0) < 3.0
    # Velocity should be approximately ~10/dt = ~300 px/s
    assert output.velocity[0] > 0.0
    assert output.velocity[1] > 0.0
    assert output.is_occluded is False
    assert len(output.future_positions) > 0


def test_kalman_occlusion_coasting():
    service.reset()
    # Initialize and establish track
    for i in range(10):
        service.update((100.0 + i * 5.0, 100.0))

    pos_before_drop = service.x[0, 0]

    # Target drops out for 5 frames (simulating occlusion / cloud)
    for _ in range(5):
        out = service.update(None)
        assert out.is_occluded is True

    # State should have coasted forward in x direction
    pos_after_drop = service.x[0, 0]
    assert pos_after_drop > pos_before_drop

    # Re-acquisition on frame 16
    out_reacq = service.update((pos_after_drop + 5.0, 100.0))
    assert out_reacq.is_occluded is False
    assert out_reacq.consecutive_misses == 0


def test_kalman_api_step_and_forecast():
    client = TestClient(app)
    res = client.post("/step", json={"measurement": [320.0, 240.0]})
    assert res.status_code == 200
    data = res.json()["data"]
    assert "position" in data
    assert "future_positions" in data

    res_fc = client.get("/forecast?steps=4")
    assert res_fc.status_code == 200
    assert len(res_fc.json()["data"]["forecast"]) == 4
