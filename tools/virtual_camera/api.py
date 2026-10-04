"""FastAPI REST API and MJPEG Video Stream for Virtual Camera."""
import asyncio
from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import numpy as np
from tools.simulator.service import SimulatorService
from tools.utilities.image_processing import encode_image_base64, encode_image_jpeg
from tools.utilities.network import json_success_response
from .service import VirtualCameraService

app = FastAPI(
    title="FSOC Virtual PTZ Camera API",
    description="Software PTZ camera with pan/tilt/zoom, optical jitter, and platform vibration.",
    version="1.0.0",
)

simulator_fallback = SimulatorService()
service = VirtualCameraService()


class PTZSpeedRequest(BaseModel):
    pan_speed_deg: float = Field(..., description="Pan angular speed in deg/s (max +-5 to 10 deg/s)")
    tilt_speed_deg: float = Field(..., description="Tilt angular speed in deg/s (max +-5 to 10 deg/s)")


class PTZPositionRequest(BaseModel):
    pan_deg: Optional[float] = None
    tilt_deg: Optional[float] = None
    zoom: Optional[float] = None


@app.get("/health")
def health():
    return json_success_response({"service": "virtual_camera", "status": "healthy"})


@app.get("/state")
def get_state():
    return json_success_response(service.get_state(), "Camera state retrieved")


@app.post("/reset")
def reset_camera():
    service.reset()
    return json_success_response(service.get_state(), "Camera reset to optical center")


@app.post("/ptz/speed")
def set_ptz_speed(req: PTZSpeedRequest):
    service.set_ptz_speed(req.pan_speed_deg, req.tilt_speed_deg)
    return json_success_response(service.get_state(), "PTZ commanded speed updated")


@app.post("/ptz/position")
def set_ptz_position(req: PTZPositionRequest):
    service.set_ptz(req.pan_deg, req.tilt_deg, req.zoom)
    return json_success_response(service.get_state(), "PTZ position updated")


@app.get("/frame")
def get_frame(format: str = Query("base64", description="'base64' or 'jpeg'")):
    # Step camera with simulator frame
    canvas = simulator_fallback.render_canvas()
    frame = service.step(1.0 / service.config.fps, canvas)

    if format.lower() == "jpeg":
        jpeg_bytes = encode_image_jpeg(frame)
        return Response(content=jpeg_bytes, media_type="image/jpeg")
    else:
        b64 = encode_image_base64(frame)
        return json_success_response(
            {
                "image_base64": b64,
                "width": service.config.resolution[0],
                "height": service.config.resolution[1],
                "camera_state": service.get_state(),
            },
            "Frame captured",
        )


@app.get("/stream")
async def mjpeg_stream():
    """Live 30 FPS MJPEG video stream accessible directly from browser or OpenCV."""

    async def frame_generator():
        interval = 1.0 / service.config.fps
        while True:
            simulator_fallback.step(interval)
            canvas = simulator_fallback.render_canvas()
            frame = service.step(interval, canvas)
            jpeg_bytes = encode_image_jpeg(frame)

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + jpeg_bytes + b"\r\n"
            )
            await asyncio.sleep(interval)

    return StreamingResponse(
        frame_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )
