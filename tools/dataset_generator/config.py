"""Configuration models for Synthetic Dataset Generator."""
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field


class DatasetGenerationRequest(BaseModel):
    dataset_name: str = Field(default="fsoc_synthetic_train", description="Target dataset folder name")
    num_frames: int = Field(default=60, ge=10, le=1000, description="Total number of frames to generate")
    motion_types: List[str] = Field(
        default=["figure_8", "circular", "straight", "sinusoidal"],
        description="Motion types to sample across frames",
    )
    weather_types: List[str] = Field(
        default=["clear", "fog", "rain", "haze", "low_light"],
        description="Weather conditions to simulate",
    )
    noise_levels: List[float] = Field(default=[0.0, 5.0, 10.0], description="Gaussian noise std dev levels")
    export_video: bool = Field(default=True, description="Whether to also encode an MP4 video clip")
    output_dir: str = Field(default="datasets", description="Root output directory")
