"""Tests for shared geometry and image processing utilities."""
import numpy as np
from tools.utilities.geometry import (
    deg2rad,
    rad2deg,
    normalize_angle,
    euclidean_distance,
    world_to_camera_pixel,
    camera_pixel_to_world,
)
from tools.utilities.image_processing import (
    encode_image_base64,
    decode_image_base64,
    draw_telemetry_hud,
)


def test_angle_conversions():
    assert abs(deg2rad(180.0) - np.pi) < 1e-6
    assert abs(rad2deg(np.pi) - 180.0) < 1e-6
    assert abs(normalize_angle(3.0 * np.pi) - np.pi) < 1e-6


def test_euclidean_distance():
    d = euclidean_distance((0, 0), (3, 4))
    assert abs(d - 5.0) < 1e-6


def test_world_to_camera_pixel_center():
    # If camera is at (1000, 1000), target is at (1000, 1000), pan=0, tilt=0
    # it must project directly onto sensor center (320, 240)
    u, v, in_fov = world_to_camera_pixel(
        target_pos=(1000.0, 1000.0),
        camera_center=(1000.0, 1000.0),
        pan_deg=0.0,
        tilt_deg=0.0,
        fov_deg=(4.0, 3.0),
        resolution=(640, 480),
    )
    assert abs(u - 320.0) < 1e-3
    assert abs(v - 240.0) < 1e-3
    assert in_fov is True


def test_image_base64_roundtrip():
    test_img = np.zeros((100, 100, 3), dtype=np.uint8)
    test_img[40:60, 40:60] = 255
    b64 = encode_image_base64(test_img)
    assert isinstance(b64, str)
    decoded = decode_image_base64(b64)
    assert decoded.shape == (100, 100, 3)


def test_draw_telemetry_hud():
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    telemetry = {
        "fps": 30.5,
        "tracking_error": 4.2,
        "locked": True,
        "lock_retention_rate": 0.98,
        "pan_deg": 1.2,
        "tilt_deg": -0.5,
    }
    annotated = draw_telemetry_hud(
        frame,
        telemetry=telemetry,
        target_pos=(324.0, 243.0),
        predicted_pos=(325.0, 244.0),
        bbox=(315, 235, 18, 18),
    )
    assert annotated.shape == (480, 640, 3)
