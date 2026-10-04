"""Configuration models for Analytics & Reporting Dashboard."""
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field


class AnalyticsReportRequest(BaseModel):
    session_name: str = Field(default="isro_benchmark_run", description="Name of simulation run")
    timestamps: List[float] = Field(default_factory=list)
    tracking_errors: List[float] = Field(default_factory=list)
    fps_values: List[float] = Field(default_factory=list)
    target_path_world: List[List[float]] = Field(default_factory=list)  # list of [x, y]
    camera_path_world: List[List[float]] = Field(default_factory=list)  # list of [x, y]
    summary_metrics: Optional[dict] = None
    output_dir: str = Field(default="outputs/reports")


class AnalyticsConfig(BaseModel):
    output_dir: str = Field(default="outputs/reports", description="Destination for generated charts and PDF reports")
    dpi: int = Field(default=150, description="DPI for exported Matplotlib figures")
    report_title: str = Field(
        default="ISRO SIH - FSOC AI Virtual Camera Tracking Benchmark Report",
        description="Title printed on PDF evaluation reports",
    )
