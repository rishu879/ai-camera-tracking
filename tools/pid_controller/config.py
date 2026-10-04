"""Configuration models for the PID Camera Controller."""
from typing import Tuple
from pydantic import BaseModel, Field


class PIDControlOutput(BaseModel):
    pan_speed_deg: float  # Commanded pan speed in deg/s
    tilt_speed_deg: float  # Commanded tilt speed in deg/s
    error_x: float  # Error in pixels (target_x - center_x)
    error_y: float  # Error in pixels (target_y - center_y)
    total_error_px: float  # Euclidean distance sqrt(ex^2 + ey^2)
    in_deadband: bool
    integral_x: float
    integral_y: float
    derivative_x: float
    derivative_y: float


class PIDConfig(BaseModel):
    kp_pan: float = Field(default=0.035, ge=0.0, le=2.0, description="Proportional gain for pan axis")
    ki_pan: float = Field(default=0.002, ge=0.0, le=0.5, description="Integral gain for pan axis")
    kd_pan: float = Field(default=0.012, ge=0.0, le=1.0, description="Derivative gain for pan axis")
    kp_tilt: float = Field(default=0.035, ge=0.0, le=2.0, description="Proportional gain for tilt axis")
    ki_tilt: float = Field(default=0.002, ge=0.0, le=0.5, description="Integral gain for tilt axis")
    kd_tilt: float = Field(default=0.012, ge=0.0, le=1.0, description="Derivative gain for tilt axis")
    max_pan_speed_deg: float = Field(default=5.0, ge=1.0, le=15.0, description="Slew clamp: max pan speed in deg/s (5-10)")
    max_tilt_speed_deg: float = Field(default=5.0, ge=1.0, le=15.0, description="Slew clamp: max tilt speed in deg/s (5-10)")
    anti_windup_limit: float = Field(default=2.0, ge=0.1, le=10.0, description="Integral accumulator saturation clamp")
    deadband_px: float = Field(default=0.5, ge=0.0, le=5.0, description="Pixel error deadband to prevent mechanical hunting")
    derivative_filter_alpha: float = Field(default=0.75, ge=0.0, le=1.0, description="Derivative low-pass filter factor")
    default_center: Tuple[float, float] = Field(default=(320.0, 240.0), description="Sensor optical boresight center (x, y)")
