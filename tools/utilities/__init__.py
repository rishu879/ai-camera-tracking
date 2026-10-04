"""Shared utilities for the FSOC Virtual Camera Tracking System."""
from .geometry import (
    world_to_camera_pixel,
    camera_pixel_to_world,
    normalize_angle,
    deg2rad,
    rad2deg,
    euclidean_distance,
)
from .image_processing import (
    encode_image_base64,
    decode_image_base64,
    encode_image_jpeg,
    draw_telemetry_hud,
)

__all__ = [
    "world_to_camera_pixel",
    "camera_pixel_to_world",
    "normalize_angle",
    "deg2rad",
    "rad2deg",
    "euclidean_distance",
    "encode_image_base64",
    "decode_image_base64",
    "encode_image_jpeg",
    "draw_telemetry_hud",
]
