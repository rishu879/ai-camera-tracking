"""Replay System Service and ISRO Benchmark-2 Video Evaluation Runner."""
import json
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np
from tools.kalman_prediction.service import KalmanPredictionService
from tools.object_detection.service import ObjectDetectionService
from tools.object_tracking.service import ObjectTrackingService
from tools.performance_monitor.service import PerformanceMonitorService
from tools.pid_controller.service import PIDCameraControlService
from .config import Benchmark2Request, ReplayConfig, ReplayControlState
from .utils import load_ground_truth, read_video_frames, render_and_export_video


class ReplaySession:
    """Maintains playback state for a recorded simulation sequence."""

    def __init__(self, session_id: str, frames: List[np.ndarray], records: List[Dict[str, Any]], fps: float = 30.0):
        self.session_id = session_id
        self.frames = frames
        self.records = records
        self.fps = fps
        self.current_frame = 0
        self.total_frames = len(frames)
        self.is_paused = True
        self.playback_speed = 1.0

    def get_current_frame(self) -> Tuple[np.ndarray, Dict[str, Any]]:
        idx = max(0, min(self.total_frames - 1, self.current_frame))
        frame = self.frames[idx] if len(self.frames) > 0 else np.zeros((480, 640), dtype=np.uint8)
        record = self.records[idx] if idx < len(self.records) else {}
        return frame, record

    def step(self, forward: bool = True) -> int:
        if forward:
            self.current_frame = min(self.total_frames - 1, self.current_frame + 1)
        else:
            self.current_frame = max(0, self.current_frame - 1)
        return self.current_frame

    def seek(self, frame_idx: int) -> int:
        self.current_frame = max(0, min(self.total_frames - 1, frame_idx))
        return self.current_frame

    def get_state(self) -> ReplayControlState:
        return ReplayControlState(
            session_id=self.session_id,
            current_frame=self.current_frame,
            total_frames=self.total_frames,
            is_paused=self.is_paused,
            playback_speed=self.playback_speed,
            fps=self.fps,
        )


class ReplayService:
    """Manages replay sessions and runs Benchmark-2 hardware-in-the-loop video evaluations."""

    def __init__(self, config: Optional[ReplayConfig] = None):
        self.config = config or ReplayConfig()
        self.sessions: Dict[str, ReplaySession] = {}
        self.active_session_id: Optional[str] = None

    def create_session(
        self, session_id: str, frames: List[np.ndarray], records: List[Dict[str, Any]], fps: float = 30.0
    ) -> ReplaySession:
        session = ReplaySession(session_id, frames, records, fps)
        self.sessions[session_id] = session
        self.active_session_id = session_id
        return session

    def run_benchmark_2(self, req: Benchmark2Request) -> Dict[str, Any]:
        """
        Execute ISRO Benchmark-2 Evaluation:
        - Ingests an external MP4 video file (@30 FPS) covering screen with noise and moving beacon spot.
        - Bypasses PTZ camera simulator and feeds raw frames directly into the coarse pointing pipeline.
        - Computes Centroiding error against ground-truth (if provided) and boresight error.
        - Evaluates RMSE, Acquisition Time, Re-acquisition Time, Lock Retention Rate, and FPS.
        - Optionally exports annotated MP4 video with aerospace HUD telemetry overlay.
        """
        video_path = Path(req.video_path)
        frames = read_video_frames(video_path)
        if len(frames) == 0:
            raise ValueError(f"No frames could be extracted from video: {video_path}")

        gt_dict = {}
        if req.ground_truth_path:
            gt_dict = load_ground_truth(Path(req.ground_truth_path))

        # Initialize perception, tracking, prediction, and PID pipelines
        detector = ObjectDetectionService()
        tracker = ObjectTrackingService()
        kalman = KalmanPredictionService()
        pid = PIDCameraControlService()
        monitor = PerformanceMonitorService()

        telemetry_records = []
        out_dir = Path(req.output_dir) / req.session_name
        out_dir.mkdir(parents=True, exist_ok=True)

        h, w = frames[0].shape[:2]
        center = (w / 2.0, h / 2.0)

        t_start = time.time()

        for idx, frame in enumerate(frames, start=1):
            f_t0 = time.perf_counter()

            # 1. Detection (YOLO / Adaptive centroiding)
            detections = detector.detect(frame)

            # 2. Tracking (ByteTrack)
            det_dicts = [
                {"bbox": d.bbox, "centroid": d.centroid, "confidence": d.confidence}
                for d in detections
            ]
            tracks = tracker.update(det_dicts)

            # 3. Kalman prediction & state estimation
            active_track = tracks[0] if len(tracks) > 0 else None
            meas = tuple(active_track.centroid) if active_track else None
            kal_out = kalman.update(meas)

            # Target position: measured centroid or kalman predicted position
            current_target = meas if meas else tuple(kal_out.position) if kalman.initialized else None

            # 4. PID control computation
            if current_target:
                pid_out = pid.compute(target_pos=current_target, desired_center=center)
                tracking_error_px = pid_out.total_error_px
                is_locked = tracking_error_px <= 10.0
            else:
                tracking_error_px = float(w)  # Max penalty if completely undetected
                is_locked = False

            f_latency = (time.perf_counter() - f_t0) * 1000.0  # ms
            instant_fps = 1000.0 / max(f_latency, 1.0)

            # Ground truth comparison if provided
            gt_error = None
            eval_error_px = tracking_error_px
            if idx in gt_dict and current_target:
                gt_pos = gt_dict[idx]
                gt_error = round(float(np.hypot(current_target[0] - gt_pos[0], current_target[1] - gt_pos[1])), 3)
                eval_error_px = gt_error

            # 5. Record frame metric
            monitor.record_frame(
                frame_idx=idx,
                fps=instant_fps,
                latency_ms=f_latency,
                tracking_error_px=eval_error_px,
                is_locked=eval_error_px <= 10.0,
                is_occluded=kal_out.is_occluded,
            )

            record = {
                "frame_idx": idx,
                "target_centroid": list(current_target) if current_target else None,
                "predicted_centroid": kal_out.future_positions[0] if kal_out.future_positions else None,
                "bbox": active_track.bbox if active_track else None,
                "tracking_error": tracking_error_px,
                "gt_centroiding_error": gt_error,
                "locked": is_locked,
                "fps": round(instant_fps, 1),
                "pan_deg": 0.0,
                "tilt_deg": 0.0,
            }
            telemetry_records.append(record)

        total_time = time.time() - t_start
        summary = monitor.get_summary()

        # Export annotated video if requested
        annotated_video_path = None
        if req.export_annotated_video:
            out_vid_file = out_dir / f"{req.session_name}_annotated.mp4"
            render_and_export_video(frames, telemetry_records, out_vid_file, fps=30.0)
            annotated_video_path = str(out_vid_file)

        # Write results JSON
        results_file = out_dir / "benchmark2_results.json"
        res_data = {
            "session_name": req.session_name,
            "input_video": str(video_path),
            "total_frames": len(frames),
            "total_runtime_sec": round(total_time, 2),
            "summary_metrics": summary.model_dump(),
            "annotated_video": annotated_video_path,
        }
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(res_data, f, indent=2)

        return res_data
