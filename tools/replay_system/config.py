"""Configuration models for the Replay System and Benchmark-2 Runner."""
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


class ReplayControlState(BaseModel):
    session_id: str
    current_frame: int
    total_frames: int
    is_paused: bool
    playback_speed: float
    fps: float


class Benchmark2Request(BaseModel):
    video_path: str = Field(..., description="Path to input .mp4 video file @ 30 FPS")
    ground_truth_path: Optional[str] = Field(None, description="Optional path to ground-truth coordinates (.csv or .json)")
    session_name: str = Field(default="benchmark_2_run", description="Evaluation session identifier")
    export_annotated_video: bool = Field(default=True, description="Export video with HUD overlay")
    output_dir: str = Field(default="outputs/benchmark2")


class ReplayConfig(BaseModel):
    sessions_dir: str = Field(default="outputs/replays", description="Storage directory for recorded simulation sessions")
    benchmark_dir: str = Field(default="outputs/benchmark2", description="Storage directory for Benchmark-2 runs")
    fps_default: float = Field(default=30.0, description="Default playback FPS")
