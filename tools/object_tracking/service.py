"""ByteTrack Object Tracking Service for continuous target association."""
from collections import deque
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from .config import TrackerConfig, TrackOutput
from .utils import compute_spatial_cost_matrix, linear_assignment


class SingleTrack:
    """Represents the multi-frame state and trajectory of an optical beacon."""

    def __init__(self, track_id: int, bbox: List[float], centroid: List[float], conf: float, history_len: int = 60):
        self.track_id = track_id
        self.bbox = list(bbox)
        self.centroid = list(centroid)
        self.confidence = float(conf)
        self.velocity = [0.0, 0.0]
        self.trajectory = deque(maxlen=history_len)
        self.trajectory.append(list(centroid))
        self.hits = 1
        self.age = 1
        self.time_since_update = 0
        self.state = "New"  # "New", "Tracked", "Lost", "Removed"

    def predict(self) -> None:
        """Propagate position linearly using estimated velocity."""
        self.age += 1
        if self.time_since_update > 0:
            # Coast forward
            self.centroid[0] += self.velocity[0]
            self.centroid[1] += self.velocity[1]
            self.bbox[0] += self.velocity[0]
            self.bbox[1] += self.velocity[1]
        self.time_since_update += 1

    def update(self, bbox: List[float], centroid: List[float], conf: float) -> None:
        """Update track with newly matched measurement and smooth velocity."""
        dt = 1.0  # Normalized per-frame
        vx_instant = (centroid[0] - self.centroid[0]) / dt
        vy_instant = (centroid[1] - self.centroid[1]) / dt

        # Exponential moving average for velocity smoothing (alpha=0.6)
        alpha = 0.6
        self.velocity[0] = alpha * vx_instant + (1.0 - alpha) * self.velocity[0]
        self.velocity[1] = alpha * vy_instant + (1.0 - alpha) * self.velocity[1]

        self.bbox = list(bbox)
        self.centroid = list(centroid)
        self.confidence = float(conf)
        self.trajectory.append(list(centroid))
        self.hits += 1
        self.time_since_update = 0
        self.state = "Tracked"

    def mark_lost(self) -> None:
        self.state = "Lost"

    def mark_removed(self) -> None:
        self.state = "Removed"


class ObjectTrackingService:
    """ByteTrack two-stage data association tracker for optical beacons."""

    def __init__(self, config: Optional[TrackerConfig] = None):
        self.config = config or TrackerConfig()
        self.tracks: List[SingleTrack] = []
        self._next_id: int = 1
        self.frame_count: int = 0

    def reset(self) -> None:
        """Clear all active and lost tracks."""
        self.tracks.clear()
        self._next_id = 1
        self.frame_count = 0

    def update(self, detections: List[Dict[str, Any]]) -> List[TrackOutput]:
        """
        Process frame detections using ByteTrack two-stage matching:
        Stage 1: Match active tracks with high-score detections
        Stage 2: Match remaining tracks with low-score detections (to survive blurs/occlusions)
        """
        self.frame_count += 1

        # 1. Predict track states forward
        for track in self.tracks:
            track.predict()

        # 2. Split detections into high-confidence and low-confidence
        high_dets = []
        low_dets = []
        for det in detections:
            conf = det.get("confidence", 1.0)
            if conf >= self.config.track_thresh:
                high_dets.append(det)
            else:
                low_dets.append(det)

        # Separate confirmed/active tracks from lost tracks
        active_tracks = [t for t in self.tracks if t.state in ("Tracked", "New")]
        lost_tracks = [t for t in self.tracks if t.state == "Lost"]
        pool_tracks = active_tracks + lost_tracks

        # --- Stage 1: Match with High Confidence Detections ---
        track_centroids = [t.centroid for t in pool_tracks]
        high_centroids = [d.get("centroid", [d["bbox"][0] + d["bbox"][2] / 2, d["bbox"][1] + d["bbox"][3] / 2]) for d in high_dets]

        cost_stage1 = compute_spatial_cost_matrix(track_centroids, high_centroids, max_dist=120.0)
        matches1, unmatched_tracks1, unmatched_high = linear_assignment(cost_stage1, threshold=self.config.match_thresh)

        for trk_idx, det_idx in matches1:
            det = high_dets[det_idx]
            pool_tracks[trk_idx].update(
                bbox=det["bbox"],
                centroid=det.get("centroid", high_centroids[det_idx]),
                conf=det.get("confidence", 1.0),
            )

        # --- Stage 2: Match Remaining Tracks with Low Confidence Detections ---
        rem_tracks = [pool_tracks[i] for i in unmatched_tracks1 if pool_tracks[i].state in ("Tracked", "New")]
        matched_in_stage2 = set()
        if len(rem_tracks) > 0 and len(low_dets) > 0:
            rem_centroids = [t.centroid for t in rem_tracks]
            low_centroids = [d.get("centroid", [d["bbox"][0] + d["bbox"][2] / 2, d["bbox"][1] + d["bbox"][3] / 2]) for d in low_dets]

            cost_stage2 = compute_spatial_cost_matrix(rem_centroids, low_centroids, max_dist=100.0)
            matches2, unmatched_rem, _ = linear_assignment(cost_stage2, threshold=self.config.match_thresh + 0.1)

            for trk_idx, det_idx in matches2:
                det = low_dets[det_idx]
                rem_tracks[trk_idx].update(
                    bbox=det["bbox"],
                    centroid=det.get("centroid", low_centroids[det_idx]),
                    conf=det.get("confidence", 0.3),
                )
                matched_in_stage2.add(id(rem_tracks[trk_idx]))

        for i in unmatched_tracks1:
            track = pool_tracks[i]
            if id(track) not in matched_in_stage2:
                track.mark_lost()

        # --- Initialize New Tracks for Unmatched High Confidence Detections ---
        for det_idx in unmatched_high:
            det = high_dets[det_idx]
            c = det.get("centroid", high_centroids[det_idx])
            new_track = SingleTrack(
                track_id=self._next_id,
                bbox=det["bbox"],
                centroid=c,
                conf=det.get("confidence", 1.0),
                history_len=self.config.trajectory_history_len,
            )
            self._next_id += 1
            if self.config.min_hits <= 1:
                new_track.state = "Tracked"
            self.tracks.append(new_track)

        # --- Prune Dead Tracks ---
        surviving_tracks = []
        for track in self.tracks:
            if track.time_since_update > self.config.max_lost_frames:
                track.mark_removed()
            else:
                surviving_tracks.append(track)
        self.tracks = surviving_tracks

        # Format output for tracked objects
        output = []
        for t in self.tracks:
            if t.state in ("Tracked", "Lost"):
                output.append(
                    TrackOutput(
                        track_id=t.track_id,
                        bbox=t.bbox,
                        centroid=[round(c, 3) for c in t.centroid],
                        velocity=[round(v, 3) for v in t.velocity],
                        confidence=round(t.confidence, 3),
                        state=t.state,
                        trajectory=[[round(p[0], 2), round(p[1], 2)] for p in t.trajectory],
                        age=t.age,
                    )
                )

        return output
