"""Configuration models for Kalman Prediction Engine."""
from typing import List, Optional
from pydantic import BaseModel, Field


class KalmanStateOutput(BaseModel):
    position: List[float]  # [x, y]
    velocity: List[float]  # [vx, vy]
    acceleration: List[float]  # [ax, ay]
    future_positions: List[List[float]]  # list of [x, y] for k steps ahead
    covariance_trace: float
    is_occluded: bool
    consecutive_misses: int


class KalmanConfig(BaseModel):
    model_type: str = Field(default="constant_acceleration", description="'constant_velocity' or 'constant_acceleration'")
    dt: float = Field(default=0.0333, ge=0.001, le=1.0, description="Time step in seconds (30 Hz = 0.0333s)")
    process_noise_std: float = Field(default=0.5, ge=0.01, le=20.0, description="Kinematic process noise standard deviation")
    measurement_noise_std: float = Field(default=1.0, ge=0.01, le=20.0, description="Sensor centroid measurement noise std")
    forecast_steps: int = Field(default=3, ge=1, le=30, description="Number of future frames to forecast")
    max_coasting_frames: int = Field(default=45, ge=5, le=150, description="Max frames to coast through occlusion before reset")
