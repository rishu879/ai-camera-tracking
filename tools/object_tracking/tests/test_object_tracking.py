"""Unit tests for Object Tracking service."""
from fastapi.testclient import TestClient
from tools.object_tracking.api import app, service


def test_tracker_health():
    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["data"]["service"] == "object_tracking"


def test_bytetrack_association_and_velocity():
    service.reset()
    # Frame 1: Detection at (100, 100)
    det1 = [{"bbox": [95, 95, 10, 10], "centroid": [100.0, 100.0], "confidence": 0.95}]
    tracks1 = service.update(det1)
    assert len(tracks1) == 1
    t1_id = tracks1[0].track_id

    # Frame 2: Target moved to (105, 102)
    det2 = [{"bbox": [100, 97, 10, 10], "centroid": [105.0, 102.0], "confidence": 0.92}]
    tracks2 = service.update(det2)
    assert len(tracks2) == 1
    assert tracks2[0].track_id == t1_id
    # Check velocity estimation
    assert tracks2[0].velocity[0] > 0.0  # moving right
    assert tracks2[0].velocity[1] > 0.0  # moving down
    assert len(tracks2[0].trajectory) == 2


def test_bytetrack_low_confidence_recovery():
    service.reset()
    # Establish track with high score
    service.update([{"bbox": [200, 200, 10, 10], "centroid": [205.0, 205.0], "confidence": 0.9}])

    # Frame 2: Target severely degraded by fog/noise, confidence drops to 0.25 (< track_thresh=0.4)
    # ByteTrack stage 2 should recover this track!
    tracks = service.update([{"bbox": [204, 204, 10, 10], "centroid": [209.0, 209.0], "confidence": 0.25}])
    assert len(tracks) == 1
    assert tracks[0].track_id == 1
    assert tracks[0].state == "Tracked"


def test_tracker_api():
    client = TestClient(app)
    payload = {
        "detections": [
            {"bbox": [50, 50, 8, 8], "centroid": [54.0, 54.0], "confidence": 0.88}
        ]
    }
    res = client.post("/track", json=payload)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["active_count"] >= 1
