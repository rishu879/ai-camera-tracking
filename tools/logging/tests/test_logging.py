"""Unit tests for Structured Logger Service."""
import shutil
from pathlib import Path
from fastapi.testclient import TestClient
from tools.logging.api import app, service
from tools.logging.config import LoggingConfig


def test_logger_lifecycle():
    client = TestClient(app)
    # Health check
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["data"]["service"] == "logger"

    # Log Event
    event_payload = {"event_type": "TEST_EVENT", "details": {"param": 42}, "severity": "INFO"}
    res_ev = client.post("/logs/event", json=event_payload)
    assert res_ev.status_code == 200
    assert res_ev.json()["data"]["event_type"] == "TEST_EVENT"

    # Log Tracking
    trk_payload = {
        "frame_idx": 1,
        "track_id": 10,
        "centroid_x": 320.5,
        "centroid_y": 240.2,
        "tracking_error": 0.54,
        "locked": True,
        "confidence": 0.98,
    }
    res_trk = client.post("/logs/tracking", json=trk_payload)
    assert res_trk.status_code == 200

    # Query Tracking Logs
    query_res = client.get("/logs/query?category=tracking&limit=10")
    assert query_res.status_code == 200
    entries = query_res.json()["data"]
    assert len(entries) >= 1
    assert entries[-1]["frame_idx"] == 1
    assert entries[-1]["locked"] is True

    # Check Stats
    stats_res = client.get("/logs/stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()["data"]
    assert "tracking" in stats
    assert stats["tracking"]["size_bytes"] > 0
