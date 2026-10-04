"""Geometry, coordinate transformation, and kinematics utilities."""
import math
from typing import Tuple, Union


def deg2rad(deg: float) -> float:
    """Convert degrees to radians."""
    return deg * (math.pi / 180.0)


def rad2deg(rad: float) -> float:
    """Convert radians to degrees."""
    return rad * (180.0 / math.pi)


def normalize_angle(angle_rad: float) -> float:
    """Normalize angle to [-pi, pi]."""
    while angle_rad > math.pi:
        angle_rad -= 2.0 * math.pi
    while angle_rad < -math.pi:
        angle_rad += 2.0 * math.pi
    return angle_rad


def euclidean_distance(
    pt1: Union[Tuple[float, float], list], pt2: Union[Tuple[float, float], list]
) -> float:
    """Compute 2D Euclidean distance between two points."""
    return math.hypot(pt1[0] - pt2[0], pt1[1] - pt2[1])


def clamp(val: float, min_val: float, max_val: float) -> float:
    """Clamp value between min_val and max_val."""
    return max(min_val, min(val, max_val))


def world_to_camera_pixel(
    target_pos: Tuple[float, float],
    camera_center: Tuple[float, float],
    pan_deg: float,
    tilt_deg: float,
    fov_deg: Tuple[float, float],
    resolution: Tuple[int, int],
    jitter: Tuple[float, float] = (0.0, 0.0),
    platform_motion: Tuple[float, float] = (0.0, 0.0),
) -> Tuple[float, float, bool]:
    """
    Project world target coordinates to camera sensor pixel coordinates.

    Args:
        target_pos: (x, y) target coordinates in world canvas
        camera_center: (cx, cy) camera optical center position in world canvas
        pan_deg: Camera pan angle in degrees (positive = right)
        tilt_deg: Camera tilt angle in degrees (positive = down)
        fov_deg: (fov_horizontal, fov_vertical) in degrees
        resolution: (width, height) in pixels (e.g. 640, 480)
        jitter: (dx, dy) instantaneous camera jitter in pixels
        platform_motion: (dx, dy) platform vibration/displacement in pixels

    Returns:
        (u, v, in_fov): pixel coordinates on sensor and boolean whether target is in FOV
    """
    cam_w, cam_h = resolution
    fov_h, fov_v = fov_deg

    # Effective scale: pixels per degree
    scale_x = cam_w / max(fov_h, 1e-6)
    scale_y = cam_h / max(fov_v, 1e-6)

    # Offset from camera position in world
    dx_world = target_pos[0] - camera_center[0]
    dy_world = target_pos[1] - camera_center[1]

    # Convert angular pan/tilt offsets into equivalent world pixel shifts
    # (or world offset converted to angular offset)
    # Using small-angle approximation linear tangent projection
    pan_shift_px = pan_deg * scale_x
    tilt_shift_px = tilt_deg * scale_y

    # Relative coordinates on sensor relative to optical axis center (cam_w / 2, cam_h / 2)
    sensor_center_x = cam_w / 2.0
    sensor_center_y = cam_h / 2.0

    u = sensor_center_x + (dx_world - pan_shift_px) + jitter[0] + platform_motion[0]
    v = sensor_center_y + (dy_world - tilt_shift_px) + jitter[1] + platform_motion[1]

    # Check bounds
    in_fov = (0.0 <= u <= cam_w) and (0.0 <= v <= cam_h)
    return u, v, in_fov


def camera_pixel_to_world(
    pixel_pos: Tuple[float, float],
    camera_center: Tuple[float, float],
    pan_deg: float,
    tilt_deg: float,
    fov_deg: Tuple[float, float],
    resolution: Tuple[int, int],
) -> Tuple[float, float]:
    """Inverse projection: maps camera sensor pixel to world canvas coordinates."""
    cam_w, cam_h = resolution
    fov_h, fov_v = fov_deg

    scale_x = cam_w / max(fov_h, 1e-6)
    scale_y = cam_h / max(fov_v, 1e-6)

    sensor_center_x = cam_w / 2.0
    sensor_center_y = cam_h / 2.0

    pan_shift_px = pan_deg * scale_x
    tilt_shift_px = tilt_deg * scale_y

    world_x = camera_center[0] + (pixel_pos[0] - sensor_center_x) + pan_shift_px
    world_y = camera_center[1] + (pixel_pos[1] - sensor_center_y) + tilt_shift_px

    return world_x, world_y
