"""Unit tests for Object Detection."""
import numpy as np
from fastapi.testclient import TestClient
from tools.object_detection.api import app, service
from tools.utilities.image_processing import encode_image_base64


def test_detector_health():
    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["data"]["service"] == "object_detection"


def test_adaptive_spot_detection():
    # Synthetic frame with dark background and a bright 10x10 square beacon spot at (320, 240)
    frame = np.full((480, 640), 20, dtype=np.uint8)
    frame[235:245, 315:325] = 255  # Spot centered at (319.5, 239.5)

    detections = service.detect(frame)
    assert len(detections) >= 1

    d0 = detections[0]
    cx, cy = d0.centroid
    # Verify sub-pixel accuracy within 1 pixel of ground truth (319.5, 239.5)
    assert abs(cx - 319.5) < 1.0
    assert abs(cy - 239.5) < 1.0
    assert d0.confidence > 0.5


def test_strategy_switching():
    client = TestClient(app)
    # Switch to hybrid
    res = client.post("/model/load", json={"model_type": "hybrid"})
    assert res.status_code == 200
    assert res.json()["data"]["active_strategy"] == "hybrid"

    # Switch to yolov11
    res2 = client.post("/model/load", json={"model_type": "yolov11"})
    assert res2.status_code == 200
    assert res2.json()["data"]["active_strategy"] == "yolov11"

    # Switch back to adaptive
    service.set_strategy("adaptive")
    assert service.active_strategy_name == "adaptive"


def test_detect_api():
    client = TestClient(app)
    frame = np.full((200, 200), 10, dtype=np.uint8)
    frame[95:105, 95:105] = 255
    b64 = encode_image_base64(frame)

    res = client.post("/detect", json={"image_base64": b64})
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["count"] >= 1
    assert len(data["detections"]) >= 1
