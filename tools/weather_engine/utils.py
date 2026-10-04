"""Atmospheric physics and optical transmission degradation models."""
import random
from typing import Tuple
import cv2
import numpy as np


def apply_fog(image: np.ndarray, density: float) -> np.ndarray:
    """
    Simulate atmospheric fog via Koschmieder optical transmission:
    I(x) = J(x) * t(x) + A * (1 - t(x))
    where t(x) is transmittance and A is atmospheric ambient airlight.
    """
    if density <= 0.0:
        return image

    d = min(1.0, max(0.0, density))
    airlight = 190.0  # Atmospheric scattering brightness
    t = math_transmittance = max(0.05, 1.0 - 0.9 * d)

    img_float = image.astype(np.float32)
    foggy = img_float * t + airlight * (1.0 - t)
    return np.clip(foggy, 0, 255).astype(np.uint8)


def apply_haze(image: np.ndarray, density: float) -> np.ndarray:
    """Simulate atmospheric aerosol haze and dynamic range compression."""
    if density <= 0.0:
        return image

    d = min(1.0, max(0.0, density))
    haze_light = 160.0
    t = max(0.15, 1.0 - 0.75 * d)

    img_float = image.astype(np.float32)
    hazed = img_float * t + haze_light * (1.0 - t)
    return np.clip(hazed, 0, 255).astype(np.uint8)


def apply_rain(image: np.ndarray, intensity: float) -> np.ndarray:
    """Generate directional rainfall droplet streaks."""
    if intensity <= 0.0:
        return image

    h, w = image.shape[:2]
    rain_mask = np.zeros((h, w), dtype=np.float32)
    num_drops = int(intensity * 1200)

    for _ in range(num_drops):
        rx = random.randint(0, w - 1)
        ry = random.randint(0, h - 1)
        length = random.randint(10, 25)
        angle_deg = 75.0  # Slight slant
        dx = int(length * 0.25)
        dy = int(length * 0.95)
        cv2.line(rain_mask, (rx, ry), (min(w - 1, rx + dx), min(h - 1, ry + dy)), 200, 1)

    # Blur rain mask to simulate motion
    rain_mask = cv2.GaussianBlur(rain_mask, (3, 7), 0)

    if len(image.shape) == 3:
        rain_mask = cv2.cvtColor(rain_mask, cv2.COLOR_GRAY2BGR)

    blended = cv2.addWeighted(image.astype(np.float32), 1.0, rain_mask, 0.4 * intensity, 0)
    return np.clip(blended, 0, 255).astype(np.uint8)


def apply_snow(image: np.ndarray, intensity: float) -> np.ndarray:
    """Generate fluttering snowflake particle occlusions."""
    if intensity <= 0.0:
        return image

    h, w = image.shape[:2]
    snow_mask = np.zeros((h, w), dtype=np.float32)
    num_flakes = int(intensity * 800)

    for _ in range(num_flakes):
        sx = random.randint(0, w - 1)
        sy = random.randint(0, h - 1)
        radius = random.randint(1, 3)
        brightness = random.randint(180, 255)
        cv2.circle(snow_mask, (sx, sy), radius, brightness, -1)

    snow_mask = cv2.GaussianBlur(snow_mask, (3, 3), 0)

    if len(image.shape) == 3:
        snow_mask = cv2.cvtColor(snow_mask, cv2.COLOR_GRAY2BGR)

    blended = cv2.addWeighted(image.astype(np.float32), 1.0, snow_mask, 0.6 * intensity, 0)
    return np.clip(blended, 0, 255).astype(np.uint8)


def apply_low_light(image: np.ndarray) -> np.ndarray:
    """Simulate night / low-light optical attenuation with non-linear gamma curve."""
    gamma = 2.2
    inv_gamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** gamma) * 120.0 for i in range(256)]).astype(np.uint8)
    return cv2.LUT(image, table)


def adjust_brightness_contrast(
    image: np.ndarray, brightness: float = 1.0, contrast: float = 1.0
) -> np.ndarray:
    """Adjust brightness and contrast scaling factors."""
    if abs(brightness - 1.0) < 1e-4 and abs(contrast - 1.0) < 1e-4:
        return image

    # out = contrast * (img - 128) + 128 + (brightness - 1.0) * 100
    img_f = image.astype(np.float32)
    adjusted = contrast * (img_f - 128.0) + 128.0 + (brightness - 1.0) * 80.0
    return np.clip(adjusted, 0, 255).astype(np.uint8)
