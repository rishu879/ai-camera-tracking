"""Configuration models for Object Tracking."""
from typing import List, Optional, Tuple
from pydantic import BaseModel, Field


class TrackOutput(BaseModel):
    track_id: int
    bbox: list  # [x, y, w, h]
    centroid: list  # [cx, cy]
    velocity: list  # [vx, vy] in pixels/frame
    confidence: float
    state: str  # "Tracked", "Lost"
    trajectory: List[list]  # list of [x, y] history points
    age: int


class TrackerConfig(BaseModel):
    tracker_type: str = Field(default="bytetrack", description="'bytetrack' or 'deepsort'")
    track_thresh: float = Field(default=0.4, ge=0.05, le=1.0, description="High-score detection threshold for stage 1")
    match_thresh: float = Field(default=0.7, ge=0.1, le=1.0, description="Matching IoU / spatial distance threshold")
    max_lost_frames: int = Field(default=30, ge=5, le=120, description="Max frame buffer to retain lost tracks")
    min_hits: int = Field(default=1, ge=1, le=10, description="Consecutive detections to confirm track")
    trajectory_history_len: int = Field(default=60, ge=10, le=500, description="Points in trajectory history buffer")
