"""Configuration models for the Virtual Environment Simulator."""
from typing import List, Optional, Tuple
from pydantic import BaseModel, Field


class TargetState(BaseModel):
    target_id: int
    x: float
    y: float
    z: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    ax: float = 0.0
    ay: float = 0.0
    size: Tuple[int, int] = (10, 10)
    shape: str = "square"
    intensity: float = 255.0
    motion_type: str = "figure_8"
    speed: float = 25.0
    active: bool = True


class SimulatorConfig(BaseModel):
    canvas_width: int = Field(default=2048, ge=1000, description="Canvas width in pixels (min 2000 per ISRO specs)")
    canvas_height: int = Field(default=2048, ge=1000, description="Canvas height in pixels (min 2000 per ISRO specs)")
    fps: float = Field(default=30.0, ge=20.0, description="Simulation physics update rate in Hz")
    background_intensity: int = Field(default=10, ge=0, le=255, description="Ambient background pixel brightness")
