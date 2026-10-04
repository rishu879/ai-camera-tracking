"""Kinematic motion equations and canvas rendering utilities for Simulator."""
import math
import random
from typing import List, Tuple
import cv2
import numpy as np


def compute_figure_8(
    t: float, center: Tuple[float, float], scale: float = 300.0, speed: float = 25.0
) -> Tuple[float, float, float, float, float, float]:
    """
    Lemniscate parametric curve for Figure-8 motion.
    x(t) = x0 + a * sin(omega * t)
    y(t) = y0 + (a / 2) * sin(2 * omega * t)
    """
    omega = speed / max(scale, 1.0)
    cx, cy = center
    a = scale
    b = scale * 0.6

    sin_wt = math.sin(omega * t)
    cos_wt = math.cos(omega * t)
    sin_2wt = math.sin(2.0 * omega * t)
    cos_2wt = math.cos(2.0 * omega * t)

    x = cx + a * sin_wt
    y = cy + (b / 2.0) * sin_2wt

    vx = a * omega * cos_wt
    vy = b * omega * cos_2wt

    ax = -a * (omega**2) * sin_wt
    ay = -2.0 * b * (omega**2) * sin_2wt

    return x, y, vx, vy, ax, ay


def compute_circular(
    t: float, center: Tuple[float, float], radius: float = 250.0, speed: float = 25.0
) -> Tuple[float, float, float, float, float, float]:
    """Circular trajectory with constant angular velocity."""
    omega = speed / max(radius, 1.0)
    cx, cy = center
    theta = omega * t

    x = cx + radius * math.cos(theta)
    y = cy + radius * math.sin(theta)

    vx = -radius * omega * math.sin(theta)
    vy = radius * omega * math.cos(theta)

    ax = -radius * (omega**2) * math.cos(theta)
    ay = -radius * (omega**2) * math.sin(theta)

    return x, y, vx, vy, ax, ay


def compute_sinusoidal(
    t: float,
    center: Tuple[float, float],
    amplitude: float = 150.0,
    speed: float = 25.0,
    wavelength: float = 500.0,
    bounds: Tuple[int, int] = (2048, 2048),
) -> Tuple[float, float, float, float, float, float]:
    """Sinusoidal trajectory with horizontal linear sweep."""
    omega = (2.0 * math.pi * speed) / max(wavelength, 1.0)
    cx, cy = center
    span_x = bounds[0] * 0.7
    # Linear sweep bouncing back and forth
    x_offset = (speed * t) % (2.0 * span_x)
    if x_offset > span_x:
        x_offset = 2.0 * span_x - x_offset
        vx = -speed
    else:
        vx = speed

    x = (cx - span_x / 2.0) + x_offset
    y = cy + amplitude * math.sin(omega * t)

    vy = amplitude * omega * math.cos(omega * t)
    ax = 0.0
    ay = -amplitude * (omega**2) * math.sin(omega * t)

    return x, y, vx, vy, ax, ay


def compute_spiral(
    t: float,
    center: Tuple[float, float],
    speed: float = 25.0,
    max_radius: float = 350.0,
) -> Tuple[float, float, float, float, float, float]:
    """Archimedean spiral trajectory that periodically resets."""
    growth_rate = 15.0  # pixels per radian
    omega = speed / 100.0
    period = (max_radius / growth_rate) / omega
    t_mod = t % period

    theta = omega * t_mod
    r = growth_rate * theta
    cx, cy = center

    x = cx + r * math.cos(theta)
    y = cy + r * math.sin(theta)

    dr_dt = growth_rate * omega
    vx = dr_dt * math.cos(theta) - r * omega * math.sin(theta)
    vy = dr_dt * math.sin(theta) + r * omega * math.cos(theta)

    ax = -2 * dr_dt * omega * math.sin(theta) - r * (omega**2) * math.cos(theta)
    ay = 2 * dr_dt * omega * math.cos(theta) - r * (omega**2) * math.sin(theta)

    return x, y, vx, vy, ax, ay


def render_beacon_target(
    canvas: np.ndarray,
    x: float,
    y: float,
    size: Tuple[int, int],
    shape: str = "square",
    intensity: float = 255.0,
) -> None:
    """Draw a single optical beacon spot on the canvas."""
    h_c, w_c = canvas.shape[:2]
    ix, iy = int(round(x)), int(round(y))
    sw, sh = size

    # Bounding region
    x1 = max(0, ix - sw // 2)
    x2 = min(w_c, ix + (sw + 1) // 2)
    y1 = max(0, iy - sh // 2)
    y2 = min(h_c, iy + (sh + 1) // 2)

    if x2 <= x1 or y2 <= y1:
        return

    if shape.lower() == "square":
        # Uniform square beacon spot (ISRO SIH default)
        val = int(min(255, max(0, intensity)))
        canvas[y1:y2, x1:x2] = np.maximum(canvas[y1:y2, x1:x2], val)
    else:
        # Gaussian laser beacon spot profile
        radius = max(sw, sh) / 2.0
        sigma = radius / 2.5
        for py in range(y1, y2):
            for px in range(x1, x2):
                dist_sq = (px - ix) ** 2 + (py - iy) ** 2
                spot_val = intensity * math.exp(-dist_sq / (2.0 * sigma * sigma))
                canvas[py, px] = min(255, int(canvas[py, px] + spot_val))
