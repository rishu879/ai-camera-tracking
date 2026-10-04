"""Configuration models for the Virtual Camera."""
from typing import Tuple
from pydantic import BaseModel, Field


class VirtualCameraConfig(BaseModel):
    camera_type: str = Field(default="monochrome", description="'monochrome' or 'color'")
    resolution: Tuple[int, int] = Field(default=(640, 480), description="(width, height) sensor pixels")
    fov: Tuple[float, float] = Field(default=(4.0, 3.0), description="(fov_h, fov_v) in degrees (default 4x3)")
    fps: float = Field(default=30.0, ge=20.0, description="Sensor readout update rate in Hz (min 30 FPS)")
    max_pan_speed_deg: float = Field(default=5.0, ge=1.0, le=15.0, description="Max pan speed in deg/s (5-10 deg/s)")
    max_tilt_speed_deg: float = Field(default=5.0, ge=1.0, le=15.0, description="Max tilt speed in deg/s (5-10 deg/s)")
    max_jitter_px: float = Field(default=5.0, ge=0.0, le=20.0, description="Max high-frequency jitter (up to +-20px)")
    platform_motion_type: str = Field(default="linear", description="'none', 'linear', 'circular', 'random', 'spiral'")
    max_platform_motion_px: float = Field(default=5.0, ge=0.0, le=20.0, description="Max platform motion drift (up to +-20px)")
    zoom: float = Field(default=1.0, ge=0.2, le=10.0, description="Optical zoom factor")
