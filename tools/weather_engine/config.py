"""Configuration models for the Atmospheric Weather Engine."""
from pydantic import BaseModel, Field


class WeatherConfig(BaseModel):
    fog_density: float = Field(default=0.0, ge=0.0, le=1.0, description="Fog scattering attenuation (0=clear, 1=dense fog)")
    rain_intensity: float = Field(default=0.0, ge=0.0, le=1.0, description="Rainfall droplet streak intensity")
    snow_intensity: float = Field(default=0.0, ge=0.0, le=1.0, description="Snowfall flutter particle intensity")
    haze_density: float = Field(default=0.0, ge=0.0, le=1.0, description="Atmospheric aerosol haze density")
    low_light: bool = Field(default=False, description="Simulate night / low-light illumination")
    brightness: float = Field(default=1.0, ge=0.1, le=2.0, description="Brightness linear scaling factor")
    contrast: float = Field(default=1.0, ge=0.1, le=2.0, description="Contrast scaling factor relative to midpoint 128")
