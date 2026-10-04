"""Unit tests for Weather Engine."""
import numpy as np
from fastapi.testclient import TestClient
from tools.utilities.image_processing import encode_image_base64
from tools.weather_engine.api import app, service


def test_weather_health():
    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["data"]["service"] == "weather_engine"


def test_weather_pipeline_processing():
    test_frame = np.full((480, 640), 100, dtype=np.uint8)
    service.reset()
    service.update_config({
        "fog_density": 0.4,
        "rain_intensity": 0.3,
        "snow_intensity": 0.2,
        "low_light": True,
        "contrast": 0.8,
    })

    degraded = service.process_frame(test_frame)
    assert degraded.shape == (480, 640)
    # The image pixel values should be modified by the atmospheric degradation
    assert not np.array_equal(degraded, test_frame)


def test_weather_api_apply():
    client = TestClient(app)
    test_frame = np.full((100, 100), 50, dtype=np.uint8)
    b64 = encode_image_base64(test_frame)

    res = client.post("/apply", json={"image_base64": b64})
    assert res.status_code == 200
    assert "image_base64" in res.json()["data"]
