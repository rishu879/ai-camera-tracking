"""Configuration models for Object Detection."""
from typing import Optional
from pydantic import BaseModel, Field


class DetectionResult(BaseModel):
    bbox: list  # [x, y, w, h] in pixels
    confidence: float
    class_id: int
    class_name: str
    centroid: list  # [cx, cy] sub-pixel coordinates


class DetectorConfig(BaseModel):
    model_type: str = Field(default="adaptive", description="'adaptive', 'yolov11', or 'hybrid'")
    confidence_threshold: float = Field(default=0.35, ge=0.01, le=1.0, description="Detection confidence threshold")
    nms_threshold: float = Field(default=0.45, ge=0.01, le=1.0, description="Non-Maximum Suppression threshold")
    min_area: int = Field(default=9, ge=1, description="Minimum beacon spot area in pixels (e.g. 3x3=9)")
    max_area: int = Field(default=900, ge=10, description="Maximum beacon spot area in pixels (e.g. 30x30=900)")
    model_path: Optional[str] = Field(default="models/yolov11_beacon.onnx", description="Weights file path for YOLOv11")
