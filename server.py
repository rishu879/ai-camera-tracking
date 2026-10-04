"""Unified Mission Control Gateway Server for FSOC Virtual Camera Tracking System."""
import asyncio
import io
import json
import os
from pathlib import Path
import threading
import time
from typing import Any, Dict, Optional

import cv2
from fastapi import FastAPI, File, HTTPException, Query, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import numpy as np
from pydantic import BaseModel, Field

from tools.analytics.config import AnalyticsReportRequest
from tools.analytics.service import AnalyticsService
from tools.configuration.service import ConfigurationService
from tools.dataset_generator.config import DatasetGenerationRequest
from tools.dataset_generator.service import DatasetGeneratorService
from tools.kalman_prediction.service import KalmanPredictionService
from tools.logging.service import LoggingService
from tools.noise_generator.service import NoiseGeneratorService
from tools.object_detection.service import ObjectDetectionService
from tools.object_tracking.service import ObjectTrackingService
from tools.performance_monitor.service import PerformanceMonitorService
from tools.pid_controller.service import PIDCameraControlService
from tools.replay_system.config import Benchmark2Request
from tools.replay_system.service import ReplayService
from tools.simulator.service import SimulatorService
from tools.utilities.image_processing import draw_telemetry_hud, encode_image_jpeg
from tools.virtual_camera.service import VirtualCameraService
from tools.weather_engine.service import WeatherEngineService

app = FastAPI(
    title="ISRO FSOC Mission Control Console",
    description="AI-Based Virtual Camera Tracking System for Coarse Alignment of Mobile FSOC Terminals",
    version="1.0.0",
)

START_TIME = time.perf_counter()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SystemRunner:
    """Continuous background loop running the closed-loop tracking simulation."""

    def __init__(self):
        self.config_service = ConfigurationService()
        self.sim = SimulatorService()
        self.cam = VirtualCameraService(canvas_center=(1024.0, 1024.0))
        self.weather = WeatherEngineService()
        self.noise = NoiseGeneratorService()
        self.detector = ObjectDetectionService()
        self.tracker = ObjectTrackingService()
        self.kalman = KalmanPredictionService()
        self.pid = PIDCameraControlService()
        self.monitor = PerformanceMonitorService()
        self.logger = LoggingService()
        self.analytics = AnalyticsService()
        self.replay = ReplayService()
        self.dataset_gen = DatasetGeneratorService()

        # Operational State
        self.is_running = True
        self.is_tracking_enabled = True
        self.is_occluded_sim = False
        self.current_frame_idx = 0
        self.latest_frame_jpeg: Optional[bytes] = None
        self.latest_telemetry: Dict[str, Any] = {}
        self.frame_lock = threading.Lock()
        self.worker_thread: Optional[threading.Thread] = None

        # Initialize simulation and launch worker loop
        self.reset_system()

    def reset_system(self):
        with self.frame_lock:
            self.sim.reset()
            self.cam.reset()
            self.tracker.reset()
            self.kalman.reset()
            self.pid.reset()
            self.monitor.reset()
            self.current_frame_idx = 0
            self.is_occluded_sim = False

        if self.worker_thread is None or not self.worker_thread.is_alive():
            self.is_running = True
            self.worker_thread = threading.Thread(target=self._loop, daemon=True)
            self.worker_thread.start()

    def _loop(self):
        fps = 30.0
        interval = 1.0 / fps
        cam_w, cam_h = self.cam.config.resolution
        boresight_center = (cam_w / 2.0, cam_h / 2.0)

        while self.is_running:
            t0 = time.perf_counter()
            try:
                self.current_frame_idx += 1

                # 1. Physics Step
                targets = self.sim.step(interval)
                target = targets[0] if len(targets) > 0 else None

                # 2. Render Canvas & Crop Sensor View
                canvas = self.sim.render_canvas()
                raw_sensor_frame = self.cam.step(interval, canvas)

                # 3. Apply Weather and Sensor Noise
                weather_frame = self.weather.process_frame(raw_sensor_frame)
                noisy_frame = self.noise.process_frame(weather_frame)

                # Simulated Cloud Occlusion
                if self.is_occluded_sim:
                    noisy_frame = np.full_like(noisy_frame, 25)

                # 4. Perception: Object Detection
                detections = self.detector.detect(noisy_frame)

                # 5. Tracking: ByteTrack
                det_dicts = [
                    {"bbox": d.bbox, "centroid": d.centroid, "confidence": d.confidence}
                    for d in detections
                ]
                tracks = self.tracker.update(det_dicts)

                # 6. State Estimation & Prediction: Kalman Filter
                active_track = tracks[0] if len(tracks) > 0 else None
                meas = tuple(active_track.centroid) if (active_track and not self.is_occluded_sim) else None
                kal_out = self.kalman.update(meas)

                # Resolve active target coordinate
                if meas:
                    current_target_pos = meas
                elif kal_out.is_occluded and self.kalman.initialized:
                    current_target_pos = tuple(kal_out.position)
                else:
                    current_target_pos = None

                # 7. Closed-Loop Servo Control: PID
                if current_target_pos and self.is_tracking_enabled:
                    pid_out = self.pid.compute(
                        target_pos=current_target_pos,
                        desired_center=boresight_center,
                        dt=interval,
                    )
                    tracking_error_px = pid_out.total_error_px
                    # Servo camera
                    self.cam.set_ptz_speed(pid_out.pan_speed_deg, pid_out.tilt_speed_deg)
                else:
                    tracking_error_px = float(cam_w)
                    if self.is_tracking_enabled:
                        self.cam.set_ptz_speed(0.0, 0.0)

                duration = time.perf_counter() - t0
                instant_fps = 1.0 / max(duration, 1e-4)
                latency_ms = duration * 1000.0
                is_locked = tracking_error_px <= 10.0 and not self.is_occluded_sim

                # 8. Record Metrics
                self.monitor.record_frame(
                    frame_idx=self.current_frame_idx,
                    fps=instant_fps,
                    latency_ms=latency_ms,
                    tracking_error_px=tracking_error_px,
                    is_locked=is_locked,
                    is_occluded=self.is_occluded_sim or kal_out.is_occluded,
                )

                # 9. Render Aerospace HUD Overlay
                tel_dict = {
                    "fps": round(instant_fps, 1),
                    "tracking_error": round(tracking_error_px, 2),
                    "locked": is_locked,
                    "lock_retention_rate": round(self.monitor.get_summary().lock_retention_rate, 3),
                    "pan_deg": round(self.cam.pan_deg, 2),
                    "tilt_deg": round(self.cam.tilt_deg, 2),
                }

                hud_frame = draw_telemetry_hud(
                    noisy_frame,
                    telemetry=tel_dict,
                    target_pos=current_target_pos,
                    predicted_pos=tuple(kal_out.future_positions[0]) if kal_out.future_positions else None,
                    bbox=tuple(active_track.bbox) if active_track else None,
                )

                jpeg_bytes = encode_image_jpeg(hud_frame, quality=80)

                with self.frame_lock:
                    self.latest_frame_jpeg = jpeg_bytes
                    self.latest_telemetry = {
                        "frame_idx": self.current_frame_idx,
                        "fps": round(instant_fps, 1),
                        "latency_ms": round(latency_ms, 1),
                        "tracking_error_px": round(tracking_error_px, 2),
                        "is_locked": is_locked,
                        "pan_deg": round(self.cam.pan_deg, 2),
                        "tilt_deg": round(self.cam.tilt_deg, 2),
                        "target_motion": self.sim.targets[0].motion_type if self.sim.targets else "unknown",
                        "target_speed": self.sim.targets[0].speed if self.sim.targets else 0.0,
                        "summary": self.monitor.get_summary().model_dump(),
                        "weather": self.weather.get_state(),
                        "noise": self.noise.get_state(),
                        "is_occluded": self.is_occluded_sim,
                        "tracking_enabled": self.is_tracking_enabled,
                    }
            except Exception as loop_err:
                import traceback
                print(f"[ERROR in _loop]: {loop_err}", flush=True)
                traceback.print_exc()

            # Maintain ~30 FPS loop rate
            elapsed = time.perf_counter() - t0
            sleep_time = max(0.001, interval - elapsed)
            time.sleep(sleep_time)


runner = SystemRunner()


# --- REST & Streaming APIs ---

class HealthResponse(BaseModel):
    status: str = "ok"
    uptime_seconds: float
    timestamp: float


class ReadinessResponse(BaseModel):
    ready: bool
    worker_alive: bool
    detector_ready: bool
    frames_processed: int
    fps: float
    tracking_error_px: float


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Liveness probe confirming the HTTP server is alive."""
    uptime = time.perf_counter() - START_TIME
    return HealthResponse(
        status="ok",
        uptime_seconds=round(uptime, 2),
        timestamp=time.time(),
    )


@app.get("/ready", response_model=ReadinessResponse)
def readiness_check():
    """Readiness probe confirming the simulation loop and detector are operational."""
    with runner.frame_lock:
        worker_alive = runner.worker_thread is not None and runner.worker_thread.is_alive()
        detector_ready = runner.detector is not None
        ready = bool(worker_alive and detector_ready)
        return ReadinessResponse(
            ready=ready,
            worker_alive=worker_alive,
            detector_ready=detector_ready,
            frames_processed=runner.current_frame_idx,
            fps=float(runner.latest_telemetry.get("fps", 0.0)),
            tracking_error_px=float(runner.latest_telemetry.get("tracking_error_px", 0.0)),
        )


@app.get("/api/stream")
def video_stream():
    """Live 30 FPS multipart MJPEG stream with aerospace HUD overlay."""
    def frame_gen():
        try:
            while True:
                with runner.frame_lock:
                    frame_bytes = runner.latest_frame_jpeg
                if frame_bytes:
                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
                    )
                time.sleep(0.033)
        except (GeneratorExit, asyncio.CancelledError, ConnectionResetError, BrokenPipeError):
            return

    return StreamingResponse(frame_gen(), media_type="multipart/x-mixed-replace; boundary=frame")


@app.get("/api/state")
def get_system_state():
    with runner.frame_lock:
        return runner.latest_telemetry


class UpdateConfigRequest(BaseModel):
    motion_type: Optional[str] = None
    target_speed: Optional[float] = None
    fog_density: Optional[float] = None
    rain_intensity: Optional[float] = None
    snow_intensity: Optional[float] = None
    haze_density: Optional[float] = None
    low_light: Optional[bool] = None
    gaussian_std: Optional[float] = None
    salt_pepper_ratio: Optional[float] = None
    poisson_enabled: Optional[bool] = None
    motion_blur_kernel: Optional[int] = None
    camera_blur_sigma: Optional[float] = None
    max_pan_speed: Optional[float] = None
    max_tilt_speed: Optional[float] = None
    is_occluded: Optional[bool] = None
    tracking_enabled: Optional[bool] = None


@app.post("/api/config/update")
def update_config(req: UpdateConfigRequest):
    with runner.frame_lock:
        if req.motion_type and runner.sim.targets:
            runner.sim.targets[0].motion_type = req.motion_type.lower()
        if req.target_speed and runner.sim.targets:
            runner.sim.targets[0].speed = req.target_speed
        if req.fog_density is not None:
            runner.weather.config.fog_density = req.fog_density
        if req.rain_intensity is not None:
            runner.weather.config.rain_intensity = req.rain_intensity
        if req.snow_intensity is not None:
            runner.weather.config.snow_intensity = req.snow_intensity
        if req.haze_density is not None:
            runner.weather.config.haze_density = req.haze_density
        if req.low_light is not None:
            runner.weather.config.low_light = req.low_light
        if req.gaussian_std is not None:
            runner.noise.config.gaussian_std = req.gaussian_std
        if req.salt_pepper_ratio is not None:
            runner.noise.config.salt_pepper_ratio = req.salt_pepper_ratio
        if req.poisson_enabled is not None:
            runner.noise.config.poisson_enabled = req.poisson_enabled
        if req.motion_blur_kernel is not None:
            runner.noise.config.motion_blur_kernel = req.motion_blur_kernel
        if req.camera_blur_sigma is not None:
            runner.noise.config.camera_blur_sigma = req.camera_blur_sigma
        if req.max_pan_speed is not None:
            runner.cam.config.max_pan_speed_deg = req.max_pan_speed
            runner.pid.config.max_pan_speed_deg = req.max_pan_speed
            runner.pid._init_controllers()
        if req.max_tilt_speed is not None:
            runner.cam.config.max_tilt_speed_deg = req.max_tilt_speed
            runner.pid.config.max_tilt_speed_deg = req.max_tilt_speed
            runner.pid._init_controllers()
        if req.is_occluded is not None:
            runner.is_occluded_sim = req.is_occluded
        if req.tracking_enabled is not None:
            runner.is_tracking_enabled = req.tracking_enabled

    return {"status": "success", "message": "Configuration updated successfully"}


@app.post("/api/system/reset")
def reset_system():
    runner.reset_system()
    return {"status": "success", "message": "System state reset"}


@app.post("/api/benchmark1/run")
def trigger_benchmark1(frames: int = Query(180)):
    from tools.orchestrator import FSOCTrackingOrchestrator
    session_id = f"benchmark1_web_{int(time.time())}"
    orch = FSOCTrackingOrchestrator(profile_name="isro_benchmark_1")
    res = orch.run_simulation(num_frames=frames, session_name=session_id, export_video=True)
    return {"status": "success", "session_id": session_id, "results": res}


@app.post("/api/benchmark2/upload")
async def upload_benchmark2_video(file: UploadFile = File(...)):
    temp_dir = Path("outputs/benchmark2_uploads")
    temp_dir.mkdir(parents=True, exist_ok=True)
    file_path = temp_dir / file.filename

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    session_id = f"bench2_{Path(file.filename).stem}_{int(time.time())}"
    req = Benchmark2Request(
        video_path=str(file_path),
        session_name=session_id,
        export_annotated_video=True,
    )
    res = runner.replay.run_benchmark_2(req)
    return {"status": "success", "session_id": session_id, "results": res}


@app.get("/api/reports/list")
def list_reports():
    reports_dir = Path("outputs/reports")
    if not reports_dir.exists():
        return []
    items = []
    for d in reports_dir.iterdir():
        if d.is_dir():
            pdf = d / f"{d.name}_report.pdf"
            html = d / f"{d.name}_dashboard.html"
            items.append({
                "session_name": d.name,
                "has_pdf": pdf.exists(),
                "has_html": html.exists(),
                "pdf_url": f"/api/reports/{d.name}/pdf" if pdf.exists() else None,
                "html_url": f"/api/reports/{d.name}/html" if html.exists() else None,
            })
    return items


@app.get("/api/reports/{session_name}/pdf")
def get_pdf_report(session_name: str):
    pdf_path = Path("outputs/reports") / session_name / f"{session_name}_report.pdf"
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF report not found")
    return FileResponse(str(pdf_path), media_type="application/pdf", filename=f"{session_name}_report.pdf")


@app.get("/api/reports/{session_name}/html")
def get_html_report(session_name: str):
    html_path = Path("outputs/reports") / session_name / f"{session_name}_dashboard.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="HTML report not found")
    return FileResponse(str(html_path), media_type="text/html")


@app.get("/api/reports/{session_name}/{filename}")
def get_report_asset(session_name: str, filename: str):
    file_path = Path("outputs/reports") / session_name / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Report asset not found")
    media_type = "image/png" if filename.endswith(".png") else "application/octet-stream"
    return FileResponse(str(file_path), media_type=media_type)



# Serve Web Mission Control Console from client/
client_dir = Path("client")
if client_dir.exists():
    app.mount("/", StaticFiles(directory="client", html=True), name="client")


if __name__ == "__main__":
    import uvicorn
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    print("================================================================")
    print(">> ISRO FSOC Mission Control Server starting...")
    print(f">> Local:         http://localhost:{port}")
    print(f">> Local Network: http://192.168.1.5:{port} (or your LAN IP)")
    print("================================================================")
    uvicorn.run("server:app", host=host, port=port, reload=False)

