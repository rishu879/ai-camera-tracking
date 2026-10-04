"""FastAPI REST API for Virtual Environment Simulator."""
from typing import Any, Dict, Optional, Tuple
from fastapi import FastAPI, HTTPException, Query, Response
from pydantic import BaseModel
from tools.utilities.image_processing import encode_image_base64, encode_image_jpeg
from tools.utilities.network import json_success_response
from .service import SimulatorService

app = FastAPI(
    title="FSOC Virtual Environment Simulator API",
    description="Microservice generating 2D/3D optical beacon environment and multi-target kinematic motions.",
    version="1.0.0",
)

service = SimulatorService()


class AddTargetRequest(BaseModel):
    shape: str = "square"
    size: Tuple[int, int] = (10, 10)
    motion_type: str = "figure_8"
    speed: float = 25.0
    intensity: float = 255.0
    initial_center: Optional[Tuple[float, float]] = None


@app.get("/health")
def health():
    return json_success_response({"service": "simulator", "status": "healthy"})


@app.post("/step")
def step_simulation(dt: Optional[float] = Query(None, description="Custom dt in seconds")):
    targets = service.step(dt)
    return json_success_response(
        {
            "frame_index": service.frame_index,
            "current_time": service.current_time,
            "targets": [t.model_dump() for t in targets],
        },
        "Simulation advanced",
    )


@app.get("/state")
def get_state():
    return json_success_response(service.get_state(), "Simulation state retrieved")


@app.post("/reset")
def reset_simulation():
    service.reset()
    return json_success_response(service.get_state(), "Simulation reset to initial state")


@app.post("/target/add")
def add_target(req: AddTargetRequest):
    tgt = service.add_target(
        shape=req.shape,
        size=req.size,
        motion_type=req.motion_type,
        speed=req.speed,
        intensity=req.intensity,
        initial_center=req.initial_center,
    )
    return json_success_response(tgt.model_dump(), "Target added successfully")


@app.get("/canvas")
def get_canvas(format: str = Query("base64", description="'base64' or 'jpeg'")):
    canvas = service.render_canvas()
    if format.lower() == "jpeg":
        jpeg_bytes = encode_image_jpeg(canvas)
        return Response(content=jpeg_bytes, media_type="image/jpeg")
    else:
        b64 = encode_image_base64(canvas)
        return json_success_response(
            {"image_base64": b64, "width": service.width, "height": service.height},
            "Canvas rendered as base64",
        )
