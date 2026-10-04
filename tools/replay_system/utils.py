"""Video I/O, HUD overlay rendering, and ground-truth parsing for Replay System."""
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np
from tools.utilities.image_processing import draw_telemetry_hud


def read_video_frames(video_path: Path, max_frames: Optional[int] = None) -> List[np.ndarray]:
    """Read frames from an MP4 video file."""
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    cap = cv2.VideoCapture(str(video_path))
    frames = []
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
        if max_frames and len(frames) >= max_frames:
            break
    cap.release()
    return frames


def load_ground_truth(gt_path: Path) -> Dict[int, Tuple[float, float]]:
    """
    Parse ground truth centroid coordinates from CSV or JSON.
    Format: frame_idx -> (cx, cy)
    """
    if not gt_path.exists():
        return {}

    gt_dict = {}
    if gt_path.suffix.lower() == ".json":
        with open(gt_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    f_idx = item.get("frame_idx", item.get("frame"))
                    cx = item.get("sensor_cx", item.get("cx", item.get("x")))
                    cy = item.get("sensor_cy", item.get("cy", item.get("y")))
                    if f_idx is not None and cx is not None and cy is not None:
                        gt_dict[int(f_idx)] = (float(cx), float(cy))
    elif gt_path.suffix.lower() in (".csv", ".txt"):
        with open(gt_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 3 and row[0].isdigit():
                    gt_dict[int(row[0])] = (float(row[1]), float(row[2]))

    return gt_dict


def render_and_export_video(
    frames: List[np.ndarray],
    telemetry_records: List[Dict[str, Any]],
    output_path: Path,
    fps: float = 30.0,
) -> str:
    """Render HUD overlays onto frames and encode to MP4."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if len(frames) == 0:
        return ""

    h, w = frames[0].shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(output_path), fourcc, fps, (w, h))

    for i, frame in enumerate(frames):
        tel = telemetry_records[i] if i < len(telemetry_records) else {}
        target_pos = tel.get("target_centroid")
        predicted_pos = tel.get("predicted_centroid")
        bbox = tel.get("bbox")

        annotated = draw_telemetry_hud(
            frame,
            telemetry=tel,
            target_pos=tuple(target_pos) if target_pos else None,
            predicted_pos=tuple(predicted_pos) if predicted_pos else None,
            bbox=tuple(bbox) if bbox else None,
        )
        if len(annotated.shape) == 2:
            annotated = cv2.cvtColor(annotated, cv2.COLOR_GRAY2BGR)

        writer.write(annotated)

    writer.release()
    return str(output_path)
