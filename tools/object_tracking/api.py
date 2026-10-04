"""FastAPI REST API for Object Tracking."""
from typing import Any, Dict, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from tools.utilities.network import json_success_response
from .service import ObjectTrackingService

app = FastAPI(
    title="FSOC Object Tracking API",
    description="ByteTrack two-stage multi-object tracker providing tracking IDs, trajectories, and velocities.",
    version="1.0.0",
)

service = ObjectTrackingService()


class TrackRequest(BaseModel):
    detections: List[Dict[str, Any]]


@app.get("/health")
def health():
    return json_success_response({"service": "object_tracking", "status": "healthy"})


@app.post("/track")
def update_tracks(req: TrackRequest):
    try:
        tracks = service.update(req.detections)
        return json_success_response(
            {"active_count": len(tracks), "tracks": [t.model_dump() for t in tracks]},
            f"Tracking updated ({len(tracks)} active)",
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/tracks")
def get_active_tracks():
    tracks = [
        {
            "track_id": t.track_id,
            "centroid": t.centroid,
            "velocity": t.velocity,
            "state": t.state,
            "trajectory_len": len(t.trajectory),
        }
        for t in service.tracks
        if t.state != "Removed"
    ]
    return json_success_response(tracks, "Active tracks")


@app.post("/reset")
def reset_tracker():
    service.reset()
    return json_success_response({}, "Tracker state reset")


@app.get("/config")
def get_tracker_config():
    return json_success_response(service.config.model_dump(), "Tracker configuration")


@app.post("/config")
def update_tracker_config(patch: Dict[str, Any]):
    current = service.config.model_dump()
    current.update(patch)
    service.config = service.config.__class__(**current)
    return json_success_response(service.config.model_dump(), "Tracker configuration updated")
