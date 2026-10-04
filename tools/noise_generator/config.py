"""Configuration models for the Noise & Disturbance Generator."""
from pydantic import BaseModel, Field


class NoiseConfig(BaseModel):
    gaussian_std: float = Field(default=0.0, ge=0.0, le=20.0, description="Gaussian noise std dev (up to 20 px per ISRO spec)")
    salt_pepper_ratio: float = Field(default=0.0, ge=0.0, le=0.10, description="Salt & Pepper noise ratio (up to 10% per ISRO spec)")
    poisson_enabled: bool = Field(default=False, description="Enable Poisson photon shot noise")
    motion_blur_kernel: int = Field(default=0, ge=0, le=25, description="Motion blur kernel size in pixels (0=disabled)")
    motion_blur_angle_deg: float = Field(default=0.0, description="Motion blur direction angle in degrees")
    camera_blur_sigma: float = Field(default=0.0, ge=0.0, le=10.0, description="Optical defocus blur sigma (0=disabled)")
