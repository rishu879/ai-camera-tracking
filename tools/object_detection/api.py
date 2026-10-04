"""FastAPI REST API for Object Detection Service."""
from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from tools.utilities.image_processing import decode_image_base64
from tools.utilities.network import json_success_response
from .service import ObjectDetectionService

app = FastAPI(
    title="FSOC Object Detection API",
    description="Microservice providing YOLOv11 and sub-pixel intensity-weighted centroiding for optical beacons.",
    version="1.0.0",
)

service = ObjectDetectionService()


class DetectRequest(BaseModel):
    image_base64: str


class LoadModelRequest(BaseModel):
    model_type: str  # "adaptive", "yolov11", "hybrid"
    model_path: Optional[str] = None


@app.get("/health")
def health():
    return json_success_response({"service": "object_detection", "status": "healthy"})


@app.post("/detect")
def detect_objects(req: DetectRequest):
    try:
        image = decode_image_base64(req.image_base64)
        results = service.detect(image)
        return json_success_response(
            {"count": len(results), "detections": [r.model_dump() for r in results]},
            f"Detected {len(results)} beacon target(s)",
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/model/load")
def load_model(req: LoadModelRequest):
    try:
        service.set_strategy(req.model_type, req.model_path)
        return json_success_response(service.get_info(), f"Switched to '{req.model_type}' strategy")
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.get("/model/current")
def get_current_model():
    return json_success_response(service.get_info(), "Active model strategy info")


@app.get("/config")
def get_detector_config():
    return json_success_response(service.config.model_dump(), "Detector configuration")


@app.post("/config")
def update_detector_config(patch: Dict[str, Any]):
    current = service.config.model_dump()
    current.update(patch)
    service.config = service.config.__class__(**current)
    return json_success_response(service.config.model_dump(), "Detector configuration updated")
