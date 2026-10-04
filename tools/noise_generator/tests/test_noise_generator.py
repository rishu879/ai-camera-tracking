"""Unit tests for Noise Generator."""
import numpy as np
from fastapi.testclient import TestClient
from tools.noise_generator.api import app, service
from tools.utilities.image_processing import encode_image_base64


def test_noise_health():
    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["data"]["service"] == "noise_generator"


def test_noise_pipeline_processing():
    test_frame = np.full((200, 200), 128, dtype=np.uint8)
    service.reset()
    service.update_config({
        "gaussian_std": 10.0,
        "salt_pepper_ratio": 0.05,
        "poisson_enabled": True,
        "motion_blur_kernel": 5,
        "camera_blur_sigma": 1.5,
    })

    noisy = service.process_frame(test_frame)
    assert noisy.shape == (200, 200)
    assert not np.array_equal(noisy, test_frame)


def test_noise_api_apply():
    client = TestClient(app)
    test_frame = np.full((100, 100), 100, dtype=np.uint8)
    b64 = encode_image_base64(test_frame)

    res = client.post("/apply", json={"image_base64": b64})
    assert res.status_code == 200
    assert "image_base64" in res.json()["data"]
