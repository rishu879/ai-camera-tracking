"""Unit tests for Replay System and Benchmark-2 Evaluation."""
from pathlib import Path
import cv2
import numpy as np
from fastapi.testclient import TestClient
from tools.replay_system.api import app, service
from tools.replay_system.config import Benchmark2Request


def test_replay_health():
    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["data"]["service"] == "replay_system"


def test_replay_session_stepping():
    # Create a dummy session of 5 frames
    frames = [np.full((480, 640), i * 40, dtype=np.uint8) for i in range(5)]
    records = [{"frame_idx": i, "test_val": i} for i in range(5)]
    service.create_session("test_session_step", frames, records, fps=30.0)

    client = TestClient(app)
    state_res = client.get("/replay/state")
    assert state_res.status_code == 200
    assert state_res.json()["data"]["total_frames"] == 5

    # Step forward
    step_res = client.post("/replay/step?forward=true")
    assert step_res.status_code == 200
    assert step_res.json()["data"]["current_frame"] == 1

    # Seek
    seek_res = client.post("/replay/seek", json={"frame_idx": 3})
    assert seek_res.status_code == 200
    assert seek_res.json()["data"]["current_frame"] == 3


def test_benchmark_2_video_evaluation(tmp_path):
    # Synthesize a small 15-frame MP4 video with a bright moving beacon spot
    vid_path = tmp_path / "test_beacon_stream.mp4"
    h, w = 480, 640
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(vid_path), fourcc, 30.0, (w, h))

    for i in range(15):
        frame = np.full((h, w, 3), 30, dtype=np.uint8)
        # Spot moving near center: (320 + i*2, 240 + i)
        cx, cy = int(320 + i * 2), int(240 + i)
        frame[cy - 5 : cy + 5, cx - 5 : cx + 5] = 255
        writer.write(frame)
    writer.release()

    req = Benchmark2Request(
        video_path=str(vid_path),
        session_name="benchmark2_unit_test",
        export_annotated_video=True,
        output_dir=str(tmp_path / "benchmarks"),
    )

    results = service.run_benchmark_2(req)
    assert results["total_frames"] == 15
    assert "summary_metrics" in results
    assert results["summary_metrics"]["mean_fps"] > 0.0
    assert Path(results["annotated_video"]).exists()
