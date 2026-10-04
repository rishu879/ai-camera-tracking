"""Configuration models for Real-time Performance Monitor."""
from typing import Optional
from pydantic import BaseModel, Field


class PerformanceMetricSample(BaseModel):
    timestamp: float
    frame_idx: int
    fps: float
    latency_ms: float
    tracking_error_px: float
    is_locked: bool
    is_occluded: bool
    cpu_percent: float
    memory_mb: float


class PerformanceSummary(BaseModel):
    total_frames: int
    mean_fps: float
    mean_latency_ms: float
    mean_tracking_error_px: float
    max_tracking_error_px: float
    rmse_px: float
    lock_retention_rate: float
    target_loss_rate: float
    acquisition_time_sec: Optional[float]
    reacquisition_time_sec: Optional[float]
    cpu_percent: float
    memory_mb: float
    compliance: dict  # Check against ISRO SIH criteria


class MonitorConfig(BaseModel):
    error_threshold_px: float = Field(default=10.0, description="Max allowed tracking error in pixels (ISRO SIH: <= 10 px)")
    fps_min: float = Field(default=20.0, description="Min processing FPS (ISRO SIH: >= 20 FPS)")
    acquisition_max_sec: float = Field(default=2.0, description="Max initial acquisition time (ISRO SIH: <= 2 sec)")
    reacquisition_max_sec: float = Field(default=1.0, description="Max re-acquisition time after dropout (ISRO SIH: <= 1 sec)")
    lock_retention_min_rate: float = Field(default=0.95, description="Min lock retention rate (ISRO SIH: Target loss < 5%, lock > 95%)")
    window_size: int = Field(default=300, description="Sliding window size for real-time statistics")
