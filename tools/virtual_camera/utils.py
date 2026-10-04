"""Virtual Camera projection, FOV cropping, jitter, and platform disturbance utilities."""
import math
import random
from typing import Tuple
import cv2
import numpy as np


def compute_jitter(max_jitter_px: float) -> Tuple[float, float]:
    """Generate high-frequency Gaussian mechanical camera jitter clamped to +-max_jitter_px."""
    if max_jitter_px <= 0.0:
        return 0.0, 0.0
    sigma = max_jitter_px / 3.0
    jx = max(-max_jitter_px, min(max_jitter_px, random.gauss(0.0, sigma)))
    jy = max(-max_jitter_px, min(max_jitter_px, random.gauss(0.0, sigma)))
    return jx, jy


def compute_platform_motion(
    t: float, motion_type: str, max_drift_px: float
) -> Tuple[float, float]:
    """Generate low-frequency structural platform vibration/drift."""
    if max_drift_px <= 0.0 or motion_type.lower() == "none":
        return 0.0, 0.0

    m_type = motion_type.lower()
    omega = 1.2  # platform natural frequency ~1.2 rad/s

    if m_type == "linear":
        dx = max_drift_px * math.sin(omega * t)
        dy = max_drift_px * 0.5 * math.sin(omega * t + math.pi / 4.0)
    elif m_type == "circular":
        dx = max_drift_px * math.cos(omega * t)
        dy = max_drift_px * math.sin(omega * t)
    elif m_type == "spiral":
        r = (t % 10.0) / 10.0 * max_drift_px
        dx = r * math.cos(omega * t)
        dy = r * math.sin(omega * t)
    elif m_type == "random":
        dx = max(-max_drift_px, min(max_drift_px, random.uniform(-max_drift_px, max_drift_px)))
        dy = max(-max_drift_px, min(max_drift_px, random.uniform(-max_drift_px, max_drift_px)))
    else:
        dx, dy = 0.0, 0.0

    return dx, dy


def extract_camera_frame(
    canvas: np.ndarray,
    camera_center: Tuple[float, float],
    pan_deg: float,
    tilt_deg: float,
    fov_deg: Tuple[float, float],
    resolution: Tuple[int, int],
    zoom: float = 1.0,
    jitter: Tuple[float, float] = (0.0, 0.0),
    platform_motion: Tuple[float, float] = (0.0, 0.0),
    camera_type: str = "monochrome",
) -> np.ndarray:
    """
    Render optical sensor FOV from virtual world canvas.
    Uses projective affine transformation to crop sensor view with pan/tilt/zoom/jitter offsets.
    """
    cam_w, cam_h = resolution
    fov_h, fov_v = fov_deg
    z = max(zoom, 0.1)

    # Scale in pixels per degree
    scale_x = (cam_w / max(fov_h, 1e-4)) * z
    scale_y = (cam_h / max(fov_v, 1e-4)) * z

    # Center of sensor in world canvas coordinates
    cx_world = camera_center[0] + (pan_deg * (cam_w / max(fov_h, 1e-4))) - (jitter[0] + platform_motion[0])
    cy_world = camera_center[1] + (tilt_deg * (cam_h / max(fov_v, 1e-4))) - (jitter[1] + platform_motion[1])

    # Affine transformation matrix mapping World -> Sensor
    # Translation: center world at (0, 0), scale, translate to (cam_w / 2, cam_h / 2)
    # sensor_x = (world_x - cx_world) * (scale_x / (cam_w / fov_h)) + cam_w / 2
    M = np.array(
        [
            [z, 0.0, (cam_w / 2.0) - z * cx_world],
            [0.0, z, (cam_h / 2.0) - z * cy_world],
        ],
        dtype=np.float32,
    )

    sensor_frame = cv2.warpAffine(
        canvas,
        M,
        (cam_w, cam_h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
    )

    if camera_type.lower() == "color" and len(sensor_frame.shape) == 2:
        sensor_frame = cv2.cvtColor(sensor_frame, cv2.COLOR_GRAY2BGR)
    elif camera_type.lower() == "monochrome" and len(sensor_frame.shape) == 3:
        sensor_frame = cv2.cvtColor(sensor_frame, cv2.COLOR_BGR2GRAY)

    return sensor_frame
