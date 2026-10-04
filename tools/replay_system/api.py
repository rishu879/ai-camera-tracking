"""FastAPI REST API for Replay System and Benchmark-2 Evaluation."""
from typing import Any, Dict
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from tools.utilities.image_processing import encode_image_base64
from tools.utilities.network import json_success_response
from .config import Benchmark2Request
from .service import ReplayService

app = FastAPI(
    title="FSOC Replay System & Benchmark-2 API",
    description="Simulation replay and Benchmark-2 external video evaluation microservice.",
    version="1.0.0",
)

service = ReplayService()


class SeekRequest(BaseModel):
    frame_idx: int


@app.get("/health")
def health():
    return json_success_response({"service": "replay_system", "status": "healthy"})


@app.get("/replay/state")
def get_replay_state():
    if not service.active_session_id or service.active_session_id not in service.sessions:
        return json_success_response({}, "No active replay session")
    sess = service.sessions[service.active_session_id]
    return json_success_response(sess.get_state().model_dump(), "Replay control state")


@app.post("/replay/step")
def step_replay(forward: bool = Query(True)):
    if not service.active_session_id or service.active_session_id not in service.sessions:
        raise HTTPException(status_code=404, detail="No active session")
    sess = service.sessions[service.active_session_id]
    curr = sess.step(forward)
    frame, rec = sess.get_current_frame()
    return json_success_response(
        {"current_frame": curr, "metadata": rec, "image_base64": encode_image_base64(frame)},
        f"Stepped to frame {curr}",
    )


@app.post("/replay/seek")
def seek_replay(req: SeekRequest):
    if not service.active_session_id or service.active_session_id not in service.sessions:
        raise HTTPException(status_code=404, detail="No active session")
    sess = service.sessions[service.active_session_id]
    curr = sess.seek(req.frame_idx)
    frame, rec = sess.get_current_frame()
    return json_success_response(
        {"current_frame": curr, "metadata": rec, "image_base64": encode_image_base64(frame)},
        f"Seeked to frame {curr}",
    )


@app.post("/benchmark2/run")
def run_benchmark2_evaluation(req: Benchmark2Request):
    try:
        results = service.run_benchmark_2(req)
        return json_success_response(results, "Benchmark-2 video evaluation completed successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
