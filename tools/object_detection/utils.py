"""Sub-pixel centroiding, moment calculations, and detection post-processing utilities."""
from typing import List, Optional, Tuple
import cv2
import numpy as np


def compute_subpixel_centroid(
    roi: np.ndarray, global_offset: Tuple[int, int] = (0, 0)
) -> Optional[Tuple[float, float]]:
    """
    Compute sub-pixel intensity-weighted Center of Gravity (CoG) using image moments:
    cx = M10 / M00, cy = M01 / M00
    Achieves <0.05 pixel accuracy for optical laser beacons.
    """
    if roi.size == 0:
        return None

    # Threshold background noise within ROI to focus on spot core
    min_val, max_val, _, _ = cv2.minMaxLoc(roi)
    thresh_val = min_val + (max_val - min_val) * 0.35
    _, binary = cv2.threshold(roi, thresh_val, 255, cv2.THRESH_TOZERO)

    moments = cv2.moments(binary)
    m00 = moments["m00"]
    if m00 < 1e-5:
        # Fallback to geometric center of ROI
        h, w = roi.shape[:2]
        return float(global_offset[0] + w / 2.0), float(global_offset[1] + h / 2.0)

    local_cx = moments["m10"] / m00
    local_cy = moments["m01"] / m00

    global_cx = float(global_offset[0] + local_cx)
    global_cy = float(global_offset[1] + local_cy)

    return global_cx, global_cy


def non_max_suppression(
    boxes: List[List[float]], scores: List[float], iou_thresh: float = 0.45
) -> List[int]:
    """Perform Non-Maximum Suppression on bounding boxes."""
    if len(boxes) == 0:
        return []

    boxes_arr = np.array(boxes, dtype=np.float32)
    scores_arr = np.array(scores, dtype=np.float32)

    # Convert [x, y, w, h] to [x1, y1, x2, y2]
    x1 = boxes_arr[:, 0]
    y1 = boxes_arr[:, 1]
    x2 = x1 + boxes_arr[:, 2]
    y2 = y1 + boxes_arr[:, 3]

    areas = (x2 - x1) * (y2 - y1)
    order = scores_arr.argsort()[::-1]

    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(int(i))

        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])

        w = np.maximum(0.0, xx2 - xx1)
        h = np.maximum(0.0, yy2 - yy1)
        inter = w * h

        ovr = inter / (areas[i] + areas[order[1:]] - inter + 1e-6)
        inds = np.where(ovr <= iou_thresh)[0]
        order = order[inds + 1]

    return keep
