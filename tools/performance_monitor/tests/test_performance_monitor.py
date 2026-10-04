"""Unit tests for Performance Monitor."""
from fastapi.testclient import TestClient
from tools.performance_monitor.api import app, service


def test_monitor_health():
    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["data"]["service"] == "performance_monitor"


def test_performance_recording_and_isro_compliance():
    service.reset()
    # Simulate 50 frames with 30 FPS, latency 12ms, error 4.5 px (ISRO compliant)
    for i in range(1, 51):
        sample = service.record_frame(
            frame_idx=i,
            fps=31.2,
            latency_ms=12.5,
            tracking_error_px=4.5 + (i % 3) * 0.5,
            is_locked=True,
            is_occluded=False,
        )
        assert sample.tracking_error_px <= 10.0

    summary = service.get_summary()
    assert summary.total_frames == 50
    assert summary.mean_fps > 20.0
    assert summary.rmse_px <= 10.0
    assert summary.lock_retention_rate >= 0.95
    assert summary.compliance["overall_status"] == "PASSED (ISRO Compliant)"


def test_monitor_api_summary():
    client = TestClient(app)
    res = client.get("/summary")
    assert res.status_code == 200
    data = res.json()["data"]
    assert "mean_fps" in data
    assert "rmse_px" in data
    assert "compliance" in data
