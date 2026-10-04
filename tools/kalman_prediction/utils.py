"""State-space matrix formulations and Kalman Filter mathematical utilities."""
from typing import Tuple
import numpy as np


def build_constant_acceleration_matrices(
    dt: float, process_noise_std: float, measurement_noise_std: float
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Construct state-space matrices for 2D Constant Acceleration (CA) model.
    State x = [px, py, vx, vy, ax, ay]^T (dim=6)
    Measurement z = [px, py]^T (dim=2)
    """
    dt2 = 0.5 * (dt**2)

    # State transition matrix F (6x6)
    F = np.array(
        [
            [1.0, 0.0, dt, 0.0, dt2, 0.0],
            [0.0, 1.0, 0.0, dt, 0.0, dt2],
            [0.0, 0.0, 1.0, 0.0, dt, 0.0],
            [0.0, 0.0, 0.0, 1.0, 0.0, dt],
            [0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    )

    # Measurement matrix H (2x6)
    H = np.array(
        [
            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
        ],
        dtype=np.float64,
    )

    # Process noise mapping matrix G (6x2)
    G = np.array(
        [
            [dt2, 0.0],
            [0.0, dt2],
            [dt, 0.0],
            [0.0, dt],
            [1.0, 0.0],
            [0.0, 1.0],
        ],
        dtype=np.float64,
    )
    Q = G @ G.T * (process_noise_std**2)

    # Measurement noise covariance R (2x2)
    R = np.eye(2, dtype=np.float64) * (measurement_noise_std**2)

    return F, H, Q, R


def build_constant_velocity_matrices(
    dt: float, process_noise_std: float, measurement_noise_std: float
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Construct state-space matrices for 2D Constant Velocity (CV) model.
    State x = [px, py, vx, vy]^T (dim=4)
    Measurement z = [px, py]^T (dim=2)
    """
    F = np.array(
        [
            [1.0, 0.0, dt, 0.0],
            [0.0, 1.0, 0.0, dt],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    )

    H = np.array(
        [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
        ],
        dtype=np.float64,
    )

    dt2 = 0.5 * (dt**2)
    G = np.array(
        [
            [dt2, 0.0],
            [0.0, dt2],
            [dt, 0.0],
            [0.0, dt],
        ],
        dtype=np.float64,
    )
    Q = G @ G.T * (process_noise_std**2)
    R = np.eye(2, dtype=np.float64) * (measurement_noise_std**2)

    return F, H, Q, R
