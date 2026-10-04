"""Discrete Kalman Filter service with multi-step prediction and occlusion coasting."""
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from .config import KalmanConfig, KalmanStateOutput
from .utils import (
    build_constant_acceleration_matrices,
    build_constant_velocity_matrices,
)


class KalmanPredictionService:
    """Kalman state estimator predicting future position, velocity, acceleration under occlusions."""

    def __init__(self, config: Optional[KalmanConfig] = None):
        self.config = config or KalmanConfig()
        self.dim = 6 if self.config.model_type == "constant_acceleration" else 4

        self.x = np.zeros((self.dim, 1), dtype=np.float64)
        self.P = np.eye(self.dim, dtype=np.float64) * 100.0
        self.initialized = False

        self.consecutive_misses = 0
        self.is_occluded = False

        self._build_matrices()

    def _build_matrices(self) -> None:
        if self.config.model_type == "constant_acceleration":
            self.F, self.H, self.Q, self.R = build_constant_acceleration_matrices(
                self.config.dt,
                self.config.process_noise_std,
                self.config.measurement_noise_std,
            )
        else:
            self.F, self.H, self.Q, self.R = build_constant_velocity_matrices(
                self.config.dt,
                self.config.process_noise_std,
                self.config.measurement_noise_std,
            )

    def reset(self) -> None:
        """Reset state vector and re-initialize high covariance."""
        self.x = np.zeros((self.dim, 1), dtype=np.float64)
        self.P = np.eye(self.dim, dtype=np.float64) * 100.0
        self.initialized = False
        self.consecutive_misses = 0
        self.is_occluded = False

    def initialize_state(self, x_init: float, y_init: float) -> None:
        """Initialize filter with first valid centroid observation."""
        self.x = np.zeros((self.dim, 1), dtype=np.float64)
        self.x[0, 0] = x_init
        self.x[1, 0] = y_init
        self.P = np.eye(self.dim, dtype=np.float64) * 1000.0
        # High confidence in initial position observation
        self.P[0, 0] = self.config.measurement_noise_std ** 2
        self.P[1, 1] = self.config.measurement_noise_std ** 2
        self.initialized = True
        self.consecutive_misses = 0
        self.is_occluded = False

    def predict(self) -> np.ndarray:
        """Time update: propagate state and covariance forward by dt."""
        if not self.initialized:
            return self.x

        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q
        return self.x

    def update(self, measurement: Optional[Tuple[float, float]]) -> KalmanStateOutput:
        """
        Measurement update step.
        If measurement is available: executes standard Kalman correction.
        If measurement is None (occlusion/dropout): executes coasting mode propagation.
        """
        if not self.initialized:
            if measurement is not None:
                self.initialize_state(measurement[0], measurement[1])
                return self.get_output()
            else:
                return self.get_output()

        # Step 1: Predict
        self.predict()

        # Step 2: Correct or Coast
        if measurement is not None:
            z = np.array([[measurement[0]], [measurement[1]]], dtype=np.float64)
            # Innovation residual
            y = z - (self.H @ self.x)
            # Innovation covariance
            S = self.H @ self.P @ self.H.T + self.R
            # Optimal Kalman Gain
            K = self.P @ self.H.T @ np.linalg.inv(S)

            # State and covariance correction (Joseph stabilized form)
            I_KH = np.eye(self.dim) - (K @ self.H)
            self.x = self.x + (K @ y)
            self.P = (I_KH @ self.P @ I_KH.T) + (K @ self.R @ K.T)

            self.consecutive_misses = 0
            self.is_occluded = False
        else:
            # Occlusion coasting mode: propagate without measurement correction
            self.consecutive_misses += 1
            self.is_occluded = True

            if self.consecutive_misses > self.config.max_coasting_frames:
                # Target considered lost beyond recovery window
                self.reset()

        return self.get_output()

    def forecast(self, steps: Optional[int] = None) -> List[List[float]]:
        """Compute future trajectory positions k steps ahead: x_{t+k} = F^k * x_t."""
        k_steps = steps if steps is not None else self.config.forecast_steps
        if not self.initialized:
            return []

        future_positions = []
        x_pred = self.x.copy()
        for _ in range(k_steps):
            x_pred = self.F @ x_pred
            future_positions.append([round(float(x_pred[0, 0]), 3), round(float(x_pred[1, 0]), 3)])

        return future_positions

    def get_output(self) -> KalmanStateOutput:
        """Format current estimated kinematic state and predictions."""
        pos = [round(float(self.x[0, 0]), 3), round(float(self.x[1, 0]), 3)]
        vel = [round(float(self.x[2, 0]), 3), round(float(self.x[3, 0]), 3)]
        acc = [
            round(float(self.x[4, 0]), 3) if self.dim >= 6 else 0.0,
            round(float(self.x[5, 0]), 3) if self.dim >= 6 else 0.0,
        ]
        trace_p = float(np.trace(self.P))

        return KalmanStateOutput(
            position=pos,
            velocity=vel,
            acceleration=acc,
            future_positions=self.forecast(),
            covariance_trace=round(trace_p, 4),
            is_occluded=self.is_occluded,
            consecutive_misses=self.consecutive_misses,
        )
