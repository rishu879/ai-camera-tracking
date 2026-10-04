"""Noise and Disturbance Generator Service."""
from typing import Any, Dict, Optional
import numpy as np
from .config import NoiseConfig
from .utils import (
    apply_camera_blur,
    apply_gaussian_noise,
    apply_motion_blur,
    apply_poisson_noise,
    apply_salt_and_pepper_noise,
)


class NoiseGeneratorService:
    """Applies sensor noise, optical blur, and impulse disturbances."""

    def __init__(self, config: Optional[NoiseConfig] = None):
        self.config = config or NoiseConfig()

    def reset(self) -> None:
        """Reset all noise and blur parameters to zero."""
        self.config = NoiseConfig()

    def update_config(self, patch: Dict[str, Any]) -> NoiseConfig:
        """Update noise configuration."""
        data = self.config.model_dump()
        data.update(patch)
        self.config = NoiseConfig(**data)
        return self.config

    def process_frame(self, image: np.ndarray) -> np.ndarray:
        """Apply sequential noise and blur degradation pipeline."""
        output = image.copy()

        # 1. Motion blur (due to fast relative movement)
        if self.config.motion_blur_kernel > 1:
            output = apply_motion_blur(
                output, self.config.motion_blur_kernel, self.config.motion_blur_angle_deg
            )

        # 2. Camera optical defocus blur
        if self.config.camera_blur_sigma > 0.0:
            output = apply_camera_blur(output, self.config.camera_blur_sigma)

        # 3. Poisson photon shot noise
        if self.config.poisson_enabled:
            output = apply_poisson_noise(output)

        # 4. Gaussian readout / thermal noise
        if self.config.gaussian_std > 0.0:
            output = apply_gaussian_noise(output, self.config.gaussian_std)

        # 5. Salt and pepper impulse noise (up to 10%)
        if self.config.salt_pepper_ratio > 0.0:
            output = apply_salt_and_pepper_noise(output, self.config.salt_pepper_ratio)

        return output

    def get_state(self) -> Dict[str, Any]:
        """Return active noise configuration."""
        return self.config.model_dump()
