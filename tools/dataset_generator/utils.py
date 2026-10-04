"""Annotation exporters for YOLO, COCO, and MOT tracking formats."""
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple
import cv2
import numpy as np


def format_yolo_label(
    bbox: Tuple[float, float, float, float],
    img_w: int,
    img_h: int,
    class_id: int = 0,
) -> str:
    """Format bounding box as normalized YOLO text line: <class> <x_c> <y_c> <w> <h>."""
    bx, by, bw, bh = bbox
    cx = (bx + bw / 2.0) / float(img_w)
    cy = (by + bh / 2.0) / float(img_h)
    nw = bw / float(img_w)
    nh = bh / float(img_h)
    return f"{class_id} {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}\n"


def create_coco_template() -> Dict[str, Any]:
    """Create base COCO dictionary."""
    return {
        "info": {"description": "FSOC Synthetic Tracking Dataset", "version": "1.0"},
        "categories": [{"id": 1, "name": "beacon_spot", "supercategory": "optical_target"}],
        "images": [],
        "annotations": [],
    }


def format_mot_line(
    frame_idx: int,
    track_id: int,
    bbox: Tuple[float, float, float, float],
    conf: float = 1.0,
) -> str:
    """Format bounding box in standard MOT (Multiple Object Tracking) format."""
    bx, by, bw, bh = bbox
    return f"{frame_idx},{track_id},{bx:.2f},{by:.2f},{bw:.2f},{bh:.2f},{conf:.2f},-1,-1,-1\n"


def export_video_clip(
    frames: List[np.ndarray], output_file: Path, fps: float = 30.0
) -> bool:
    """Encode image sequence into MP4 video."""
    if len(frames) == 0:
        return False

    output_file.parent.mkdir(parents=True, exist_ok=True)
    h, w = frames[0].shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(output_file), fourcc, fps, (w, h))

    for frame in frames:
        if len(frame.shape) == 2:
            f_bgr = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        else:
            f_bgr = frame
        writer.write(f_bgr)

    writer.release()
    return True
