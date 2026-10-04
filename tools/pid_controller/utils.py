"""PID mathematical utilities, anti-windup clamping, and derivative filtering."""
from typing import Tuple
import numpy as np


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min_val and max_val."""
    return max(min_val, min(max_val, value))


def apply_deadband(error: float, deadband: float) -> float:
    """Zero out error if within deadband to prevent motor hunting and mechanical jitter."""
    if abs(error) <= deadband:
        return 0.0
    return error


def filter_derivative(
    current_raw_deriv: float, prev_filtered_deriv: float, alpha: float
) -> float:
    """
    Low-pass filter derivative term to eliminate high-frequency noise amplification:
    D_filt = alpha * D_prev + (1 - alpha) * D_raw
    """
    return alpha * prev_filtered_deriv + (1.0 - alpha) * current_raw_deriv
