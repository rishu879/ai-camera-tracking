"""Master Pipeline Orchestrator running closed-loop FSOC tracking and evaluation."""
import argparse
import json
from pathlib import Path
import time
from typing import Any, Dict, Optional
import numpy as np

from tools.analytics.config import AnalyticsReportRequest
from tools.analytics.service import AnalyticsService
from tools.configuration.service import ConfigurationService
from tools.kalman_prediction.service import KalmanPredictionService
from tools.logging.service import LoggingService
from tools.noise_generator.service import NoiseGeneratorService
from tools.object_detection.service import ObjectDetectionService
from tools.object_tracking.service import ObjectTrackingService
from tools.performance_monitor.service import PerformanceMonitorService
from tools.pid_controller.service import PIDCameraControlService
from tools.replay_system.utils import render_and_export_video
from tools.simulator.service import SimulatorService
from tools.utilities.geometry import world_to_camera_pixel
from tools.virtual_camera.service import VirtualCameraService
from tools.weather_engine.service import WeatherEngineService


class FSOCTrackingOrchestrator:
    """Orchestrates closed-loop optical beacon simulation, perception, and visual servoing."""

    def __init__(self, profile_name: str = "default", output_dir: str = "outputs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 1. Configuration & Logging
        self.config_service = ConfigurationService()
        if profile_name != "default":
            self.config_service.load_profile(profile_name)
        self.cfg = self.config_service.get_config()

        self.logger = LoggingService()
        self.monitor = PerformanceMonitorService()
        self.analytics = AnalyticsService()

        # 2. Simulation & Camera
        self.sim = SimulatorService()
        self.sim.width = self.cfg.screen.width
        self.sim.height = self.cfg.screen.height
        self.sim.fps = self.cfg.camera.fps

        self.cam = VirtualCameraService(canvas_center=(self.sim.width / 2.0, self.sim.height / 2.0))
        self.cam.config.resolution = self.cfg.camera.resolution
        self.cam.config.fov = self.cfg.camera.fov
        self.cam.config.fps = self.cfg.camera.fps
        self.cam.config.max_pan_speed_deg = self.cfg.camera.max_pan_speed
        self.cam.config.max_tilt_speed_deg = self.cfg.camera.max_tilt_speed
        self.cam.config.max_jitter_px = self.cfg.camera.jitter_max_px
        self.cam.config.platform_motion_type = self.cfg.camera.platform_motion_type
        self.cam.config.max_platform_motion_px = self.cfg.camera.platform_motion_max_px

        # 3. Disturbances
        self.weather = WeatherEngineService()
        self.weather.update_config(self.cfg.weather.model_dump())

        self.noise = NoiseGeneratorService()
        self.noise.update_config(self.cfg.noise.model_dump())

        # 4. Perception & Control
        self.detector = ObjectDetectionService()
        self.detector.set_strategy(self.cfg.detector.model_type)

        self.tracker = ObjectTrackingService()
        self.kalman = KalmanPredictionService()
        self.pid = PIDCameraControlService()

    def run_simulation(
        self,
        num_frames: int = 300,
        session_name: str = "isro_benchmark_run",
        export_video: bool = True,
        simulate_occlusion_interval: Optional[tuple] = (120, 150),
    ) -> Dict[str, Any]:
        """
        Run complete closed-loop coarse alignment tracking simulation.

        Args:
            num_frames: Total simulation frames (300 frames = 10s @ 30 FPS)
            session_name: Identifier for reports and artifacts
            export_video: Whether to export annotated MP4 video
            simulate_occlusion_interval: Optional (start_frame, end_frame) to test occlusion recovery
        """
        print(f"\n========================================================")
        print(f" Starting FSOC Coarse Alignment Simulation: '{session_name}'")
        print(f" Frames: {num_frames} | Target Motion: {self.cfg.target.motion_type}")
        print(f" Max Slew Speed: {self.cam.config.max_pan_speed_deg} deg/s | Target Lock Bound: <=10 px")
        print(f"========================================================\n")

        self.sim.reset()
        self.cam.reset()
        self.tracker.reset()
        self.kalman.reset()
        self.pid.reset()
        self.monitor.reset()

        # Set initial target motion from config
        self.sim.targets[0].motion_type = self.cfg.target.motion_type
        self.sim.targets[0].speed = self.cfg.target.speed

        session_out_dir = self.output_dir / session_name
        session_out_dir.mkdir(parents=True, exist_ok=True)

        frames_recorded = []
        telemetry_records = []
        timestamps = []
        errors = []
        fps_history = []
        target_path_world = []
        camera_path_world = []

        cam_w, cam_h = self.cam.config.resolution
        boresight_center = (cam_w / 2.0, cam_h / 2.0)
        dt = 1.0 / self.cam.config.fps

        t_sim_start = time.time()

        for f_idx in range(1, num_frames + 1):
            t_frame_start = time.perf_counter()

            # 1. Simulator step
            targets = self.sim.step(dt)
            target = targets[0]
            target_path_world.append([target.x, target.y])

            # World position of camera boresight center
            scale_x = cam_w / self.cam.config.fov[0]
            scale_y = cam_h / self.cam.config.fov[1]
            cam_world_x = self.cam.canvas_center[0] + self.cam.pan_deg * scale_x
            cam_world_y = self.cam.canvas_center[1] + self.cam.tilt_deg * scale_y
            camera_path_world.append([cam_world_x, cam_world_y])

            # 2. Render canvas & capture camera sensor FOV
            canvas = self.sim.render_canvas()
            raw_frame = self.cam.step(dt, canvas)

            # 3. Environmental disturbances
            weather_frame = self.weather.process_frame(raw_frame)
            noisy_frame = self.noise.process_frame(weather_frame)

            # Inject synthetic occlusion (cloud/dropout) if within interval
            is_occluded_interval = False
            if (
                simulate_occlusion_interval
                and simulate_occlusion_interval[0] <= f_idx <= simulate_occlusion_interval[1]
            ):
                is_occluded_interval = True
                # Blank out beacon spot region to simulate dense cloud cover
                noisy_frame = np.full_like(noisy_frame, 30)

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
            meas = tuple(active_track.centroid) if (active_track and not is_occluded_interval) else None
            kal_state = self.kalman.update(meas)

            # Determine best target centroid candidate:
            # Measured if detected, otherwise Kalman predicted position if coasting through occlusion
            if meas:
                current_target_pos = meas
            elif kal_state.is_occluded and self.kalman.initialized:
                current_target_pos = tuple(kal_state.position)
            else:
                current_target_pos = None

            # 7. Closed-Loop Control: PID Gimbal Servoing
            if current_target_pos:
                pid_cmd = self.pid.compute(
                    target_pos=current_target_pos,
                    desired_center=boresight_center,
                    dt=dt,
                )
                tracking_error_px = pid_cmd.total_error_px
                # Feed commanded angular speed directly back into virtual PTZ camera!
                self.cam.set_ptz_speed(pid_cmd.pan_speed_deg, pid_cmd.tilt_speed_deg)
            else:
                # No target detected or coasting
                tracking_error_px = float(cam_w)
                self.cam.set_ptz_speed(0.0, 0.0)

            f_duration = time.perf_counter() - t_frame_start
            instant_fps = 1.0 / max(f_duration, 1e-4)
            latency_ms = f_duration * 1000.0

            is_locked = tracking_error_px <= 10.0 and not is_occluded_interval

            # 8. Performance Monitoring & Logging
            self.monitor.record_frame(
                frame_idx=f_idx,
                fps=instant_fps,
                latency_ms=latency_ms,
                tracking_error_px=tracking_error_px,
                is_locked=is_locked,
                is_occluded=is_occluded_interval or kal_state.is_occluded,
            )

            # Append to history buffers
            sim_timestamp = round((f_idx - 1) * dt, 4)
            timestamps.append(sim_timestamp)
            errors.append(tracking_error_px)
            fps_history.append(instant_fps)

            rec = {
                "frame_idx": f_idx,
                "fps": round(instant_fps, 1),
                "tracking_error": round(tracking_error_px, 2),
                "locked": is_locked,
                "pan_deg": round(self.cam.pan_deg, 2),
                "tilt_deg": round(self.cam.tilt_deg, 2),
                "target_centroid": list(current_target_pos) if current_target_pos else None,
                "predicted_centroid": kal_state.future_positions[0] if kal_state.future_positions else None,
                "bbox": active_track.bbox if active_track else None,
            }
            telemetry_records.append(rec)

            if export_video:
                frames_recorded.append(noisy_frame)

            if f_idx % 60 == 0 or f_idx == num_frames:
                status_txt = "LOCKED" if is_locked else "SEARCHING"
                print(
                    f"Frame {f_idx:03d}/{num_frames} | Error: {tracking_error_px:5.2f} px | "
                    f"FPS: {instant_fps:4.1f} | Slew: ({self.cam.pan_deg:+5.2f}*, {self.cam.tilt_deg:+5.2f}*) | {status_txt}"
                )

        total_sim_time = time.time() - t_sim_start
        summary = self.monitor.get_summary()

        print(f"\n========================================================")
        print(f" Simulation Complete in {total_sim_time:.2f}s")
        print(f" Mean Tracking Error : {summary.mean_tracking_error_px:.2f} px")
        print(f" RMSE                : {summary.rmse_px:.2f} px (ISRO Spec: <= 10.0 px)")
        print(f" Lock Retention Rate : {summary.lock_retention_rate * 100.0:.1f}% (ISRO Spec: > 95%)")
        print(f" Acquisition Time    : {summary.acquisition_time_sec} s (ISRO Spec: <= 2.0 s)")
        print(f" Re-acquisition Time : {summary.reacquisition_time_sec} s (ISRO Spec: <= 1.0 s)")
        print(f" Average Speed       : {summary.mean_fps:.1f} FPS (ISRO Spec: >= 20.0 FPS)")
        print(f" Overall Status      : {summary.compliance.get('overall_status')}")
        print(f"========================================================\n")

        # 9. Export Annotated Telemetry Video
        video_out_path = None
        if export_video and len(frames_recorded) > 0:
            print("Encoding annotated telemetry video with aerospace HUD overlay...")
            vid_file = session_out_dir / f"{session_name}_flight.mp4"
            render_and_export_video(frames_recorded, telemetry_records, vid_file, fps=self.cam.config.fps)
            video_out_path = str(vid_file)
            print(f"Video saved: {video_out_path}")

        # 10. Generate Analytics Plots and Evaluation PDF Report
        print("Generating diagnostic plots and ISRO evaluation report...")
        report_req = AnalyticsReportRequest(
            session_name=session_name,
            timestamps=timestamps,
            tracking_errors=errors,
            fps_values=fps_history,
            target_path_world=target_path_world,
            camera_path_world=camera_path_world,
            summary_metrics=summary.model_dump(),
            output_dir=str(self.output_dir / "reports"),
        )
        report_res = self.analytics.generate_report(report_req)
        print(f"PDF Report generated : {report_res['pdf_report']}")
        print(f"HTML Dashboard       : {report_res['html_dashboard']}")

        return {
            "session_name": session_name,
            "total_frames": num_frames,
            "summary": summary.model_dump(),
            "pdf_report": report_res["pdf_report"],
            "html_dashboard": report_res["html_dashboard"],
            "video_path": video_out_path,
        }


def main():
    parser = argparse.ArgumentParser(description="FSOC Closed-Loop Camera Tracking System Orchestrator")
    parser.add_argument("--profile", default="isro_benchmark_1", help="Profile to load (e.g. isro_benchmark_1, default)")
    parser.add_argument("--frames", type=int, default=180, help="Number of simulation frames to run (180 frames = 6s)")
    parser.add_argument("--session", default="isro_benchmark_1_eval", help="Session output name")
    parser.add_argument("--no-video", action="store_true", help="Skip MP4 video rendering")
    args = parser.parse_args()

    orchestrator = FSOCTrackingOrchestrator(profile_name=args.profile)
    orchestrator.run_simulation(
        num_frames=args.frames,
        session_name=args.session,
        export_video=not args.no_video,
    )


if __name__ == "__main__":
    main()
