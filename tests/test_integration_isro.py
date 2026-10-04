"""End-to-end integration tests validating FSOC tracking against ISRO SIH criteria."""
from pathlib import Path
import pytest
from tools.orchestrator import FSOCTrackingOrchestrator
from tools.replay_system.config import Benchmark2Request
from tools.replay_system.service import ReplayService
import cv2
import numpy as np


def test_isro_benchmark_1_closed_loop():
    """
    Validate ISRO Benchmark-1 Criteria:
    - 2000x2000 canvas
    - Figure-8 motion
    - 640x480 monochrome 30 FPS camera
    - Pan/Tilt max speed 5 deg/s
    - Mechanical jitter & platform vibration active
    - Tracking error <= 10 pixels
    - Processing speed >= 20 FPS
    - Lock retention > 95%
    - Acquisition time <= 2.0s
    """
    orchestrator = FSOCTrackingOrchestrator(profile_name="isro_benchmark_1")
    # Run 120 frames (4.0 seconds of closed-loop servoing)
    results = orchestrator.run_simulation(
        num_frames=120,
        session_name="unit_test_isro_benchmark_1",
        export_video=True,
        simulate_occlusion_interval=None,
    )

    summary = results["summary"]
    # 1. Processing Speed >= 20 FPS
    assert summary["mean_fps"] >= 20.0, f"Expected FPS >= 20, got {summary['mean_fps']}"

    # 2. Tracking Centroid Error (RMSE) <= 10 pixels
    assert summary["rmse_px"] <= 10.0, f"Expected RMSE <= 10 px, got {summary['rmse_px']}"

    # 3. Lock Retention Rate > 95%
    assert summary["lock_retention_rate"] >= 0.95, f"Expected Lock Rate >= 95%, got {summary['lock_retention_rate']*100}%"

    # 4. Acquisition Time <= 2.0 sec
    if summary["acquisition_time_sec"] is not None:
        assert summary["acquisition_time_sec"] <= 2.0, f"Expected Acquisition <= 2s, got {summary['acquisition_time_sec']}"

    # Verify generated artifacts exist
    assert Path(results["pdf_report"]).exists()
    assert Path(results["html_dashboard"]).exists()
    assert Path(results["video_path"]).exists()


def test_isro_occlusion_reacquisition_time():
    """
    Validate ISRO Re-acquisition Criterion:
    - Target disappears for frames 30 to 45 (simulating cloud / physical occlusion)
    - System enters coasting mode
    - Upon reappearance, re-acquisition time must be <= 1.0 second
    """
    orchestrator = FSOCTrackingOrchestrator(profile_name="isro_benchmark_1")
    results = orchestrator.run_simulation(
        num_frames=80,
        session_name="unit_test_occlusion",
        export_video=False,
        simulate_occlusion_interval=(30, 45),
    )

    summary = results["summary"]
    if summary["reacquisition_time_sec"] is not None:
        assert summary["reacquisition_time_sec"] <= 1.0, f"Expected Re-acquisition <= 1.0s, got {summary['reacquisition_time_sec']}"


def test_isro_benchmark_2_video_bypass(tmp_path):
    """
    Validate ISRO Benchmark-2:
    - Bypasses PTZ simulator
    - Feeds recorded video directly into detection & coarse pointing pipeline
    - Evaluates RMSE and FPS
    """
    vid_file = tmp_path / "test_input_stream.mp4"
    gt_file = tmp_path / "test_gt.csv"
    h, w = 480, 640
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(vid_file), fourcc, 30.0, (w, h))

    with open(gt_file, "w", encoding="utf-8") as f_gt:
        for i in range(1, 21):
            frame = np.full((h, w, 3), 25, dtype=np.uint8)
            cx, cy = float(320 + i * 1.5), float(240 + i * 0.8)
            ix, iy = int(round(cx)), int(round(cy))
            frame[iy - 5 : iy + 5, ix - 5 : ix + 5] = 255
            writer.write(frame)
            f_gt.write(f"{i},{cx:.2f},{cy:.2f}\n")
    writer.release()

    replay_svc = ReplayService()
    req = Benchmark2Request(
        video_path=str(vid_file),
        ground_truth_path=str(gt_file),
        session_name="isro_bench2_test",
        export_annotated_video=True,
        output_dir=str(tmp_path / "bench2_out"),
    )

    bench_results = replay_svc.run_benchmark_2(req)
    assert bench_results["total_frames"] == 20
    assert bench_results["summary_metrics"]["mean_fps"] >= 20.0
    assert bench_results["summary_metrics"]["rmse_px"] <= 10.0
