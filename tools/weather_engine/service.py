"""Atmospheric Weather Engine Service."""
from typing import Any, Dict, Optional
import numpy as np
from .config import WeatherConfig
from .utils import (
    adjust_brightness_contrast,
    apply_fog,
    apply_haze,
    apply_low_light,
    apply_rain,
    apply_snow,
)


class WeatherEngineService:
    """Simulates atmospheric disturbances and optical scattering effects."""

    def __init__(self, config: Optional[WeatherConfig] = None):
        self.config = config or WeatherConfig()

    def reset(self) -> None:
        """Reset weather to clear conditions."""
        self.config = WeatherConfig()

    def update_config(self, patch: Dict[str, Any]) -> WeatherConfig:
        """Update weather parameters."""
        data = self.config.model_dump()
        data.update(patch)
        self.config = WeatherConfig(**data)
        return self.config

    def process_frame(self, image: np.ndarray) -> np.ndarray:
        """Apply complete atmospheric weather degradation pipeline to input frame."""
        output = image.copy()

        # 1. Low light / Night
        if self.config.low_light:
            output = apply_low_light(output)

        # 2. Atmospheric haze
        if self.config.haze_density > 0.0:
            output = apply_haze(output, self.config.haze_density)

        # 3. Dense fog
        if self.config.fog_density > 0.0:
            output = apply_fog(output, self.config.fog_density)

        # 4. Rain
        if self.config.rain_intensity > 0.0:
            output = apply_rain(output, self.config.rain_intensity)

        # 5. Snow
        if self.config.snow_intensity > 0.0:
            output = apply_snow(output, self.config.snow_intensity)

        # 6. Brightness and contrast
        output = adjust_brightness_contrast(output, self.config.brightness, self.config.contrast)

        return output

    def get_state(self) -> Dict[str, Any]:
        """Return current weather settings."""
        return self.config.model_dump()
