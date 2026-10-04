"""Data association, cost matrix computation, and Hungarian matching utilities."""
from typing import List, Tuple
import numpy as np
from scipy.optimize import linear_sum_assignment


def compute_iou_matrix(boxes_a: List[List[float]], boxes_b: List[List[float]]) -> np.ndarray:
    """Compute pairwise Intersection over Union (IoU) matrix."""
    if len(boxes_a) == 0 or len(boxes_b) == 0:
        return np.empty((len(boxes_a), len(boxes_b)), dtype=np.float32)

    a = np.array(boxes_a, dtype=np.float32)
    b = np.array(boxes_b, dtype=np.float32)

    # Convert [x, y, w, h] to [x1, y1, x2, y2]
    a_x1, a_y1, a_x2, a_y2 = a[:, 0], a[:, 1], a[:, 0] + a[:, 2], a[:, 1] + a[:, 3]
    b_x1, b_y1, b_x2, b_y2 = b[:, 0], b[:, 1], b[:, 0] + b[:, 2], b[:, 1] + b[:, 3]

    area_a = (a_x2 - a_x1) * (a_y2 - a_y1)
    area_b = (b_x2 - b_x1) * (b_y2 - b_y1)

    xx1 = np.maximum(a_x1[:, None], b_x1[None, :])
    yy1 = np.maximum(a_y1[:, None], b_y1[None, :])
    xx2 = np.minimum(a_x2[:, None], b_x2[None, :])
    yy2 = np.minimum(a_y2[:, None], b_y2[None, :])

    w = np.maximum(0.0, xx2 - xx1)
    h = np.maximum(0.0, yy2 - yy1)
    inter = w * h

    union = area_a[:, None] + area_b[None, :] - inter
    iou = inter / np.maximum(union, 1e-6)
    return iou


def compute_spatial_cost_matrix(
    track_centroids: List[List[float]], det_centroids: List[List[float]], max_dist: float = 100.0
) -> np.ndarray:
    """
    Compute Euclidean distance cost matrix between centroids, normalized by max_dist.
    Cost in range [0, 1]. For small beacon spots, spatial centroid distance is often
    superior to IoU when spot sizes are small (e.g. 5x5 to 10x10 px).
    """
    if len(track_centroids) == 0 or len(det_centroids) == 0:
        return np.empty((len(track_centroids), len(det_centroids)), dtype=np.float32)

    tc = np.array(track_centroids, dtype=np.float32)
    dc = np.array(det_centroids, dtype=np.float32)

    # Euclidean distance
    diff = tc[:, None, :] - dc[None, :, :]
    dist = np.hypot(diff[:, :, 0], diff[:, :, 1])

    # Convert distance to cost [0, 1]
    cost = dist / max(max_dist, 1.0)
    cost[dist > max_dist] = 1.0  # Cap at 1.0
    return cost


def linear_assignment(
    cost_matrix: np.ndarray, threshold: float
) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
    """
    Solve linear assignment problem with gating threshold using Hungarian algorithm.

    Returns:
        matches: list of (track_idx, det_idx)
        unmatched_tracks: list of track indices
        unmatched_dets: list of detection indices
    """
    if cost_matrix.size == 0:
        return [], list(range(cost_matrix.shape[0])), list(range(cost_matrix.shape[1]))

    row_ind, col_ind = linear_sum_assignment(cost_matrix)

    matches = []
    unmatched_tracks = list(range(cost_matrix.shape[0]))
    unmatched_dets = list(range(cost_matrix.shape[1]))

    for r, c in zip(row_ind, col_ind):
        if cost_matrix[r, c] <= threshold:
            matches.append((int(r), int(c)))
            if int(r) in unmatched_tracks:
                unmatched_tracks.remove(int(r))
            if int(c) in unmatched_dets:
                unmatched_dets.remove(int(c))

    return matches, unmatched_tracks, unmatched_dets
