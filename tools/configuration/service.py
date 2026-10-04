"""Configuration Service implementing business logic for configuration management."""
from pathlib import Path
from typing import Any, Dict, Optional
from .config import SystemConfig
from .utils import load_yaml_file, save_yaml_file, load_json_file, save_json_file


class ConfigurationService:
    """Manages system configuration lifecycle, schema validation, and profiles."""

    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path(__file__).parent / "presets"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._active_config: SystemConfig = SystemConfig()
        self._init_preset_profiles()

    def _init_preset_profiles(self) -> None:
        """Create standard preset profiles if they don't exist."""
        # 1. Default Profile
        default_file = self.config_dir / "default.yaml"
        if not default_file.exists():
            save_yaml_file(default_file, self._active_config.model_dump())

        # 2. ISRO Benchmark 1 Profile (Mandatory SIH specifications)
        # 2000x2000 canvas, Figure-8 motion, 640x480 monochrome 30 FPS, Max Pan/Tilt 5 deg/s,
        # Jitter +-5px, Linear platform motion +-5px
        isro1_file = self.config_dir / "isro_benchmark_1.yaml"
        if not isro1_file.exists():
            cfg1 = SystemConfig(
                profile_name="isro_benchmark_1",
                screen={"width": 2048, "height": 2048},
                target={
                    "num_targets": 1,
                    "shape": "square",
                    "size": [10, 10],
                    "motion_type": "figure_8",
                    "speed": 30.0,
                    "intensity": 255.0,
                },
                camera={
                    "camera_type": "monochrome",
                    "resolution": [640, 480],
                    "fov": [4.0, 3.0],
                    "fps": 30.0,
                    "max_pan_speed": 5.0,
                    "max_tilt_speed": 5.0,
                    "jitter_max_px": 5.0,
                    "platform_motion_type": "linear",
                    "platform_motion_max_px": 5.0,
                },
                weather={"fog_density": 0.0, "low_light": False, "brightness": 1.0, "contrast": 1.0},
                noise={"gaussian_std": 2.0, "salt_pepper_ratio": 0.01},
            )
            save_yaml_file(isro1_file, cfg1.model_dump())

        # 3. ISRO Benchmark 2 Profile (Bypass PTZ, external video input evaluation)
        isro2_file = self.config_dir / "isro_benchmark_2.yaml"
        if not isro2_file.exists():
            cfg2 = SystemConfig(
                profile_name="isro_benchmark_2",
                screen={"width": 2048, "height": 2048},
                target={"num_targets": 1, "shape": "square", "size": [10, 10], "motion_type": "straight"},
                camera={"camera_type": "monochrome", "resolution": [640, 480], "fps": 30.0},
                noise={"gaussian_std": 10.0, "salt_pepper_ratio": 0.05},
            )
            save_yaml_file(isro2_file, cfg2.model_dump())

        # 4. Harsh Environment Profile (Heavy fog, rain, low-light, high noise & jitter)
        harsh_file = self.config_dir / "harsh_environment.yaml"
        if not harsh_file.exists():
            cfg_harsh = SystemConfig(
                profile_name="harsh_environment",
                camera={"jitter_max_px": 15.0, "platform_motion_max_px": 15.0},
                weather={
                    "fog_density": 0.5,
                    "rain_intensity": 0.4,
                    "low_light": True,
                    "brightness": 0.6,
                    "contrast": 0.7,
                },
                noise={"gaussian_std": 15.0, "salt_pepper_ratio": 0.08, "poisson_enabled": True},
            )
            save_yaml_file(harsh_file, cfg_harsh.model_dump())

    def get_config(self) -> SystemConfig:
        """Return the current active system configuration."""
        return self._active_config

    def get_config_dict(self) -> Dict[str, Any]:
        """Return active config as dictionary."""
        return self._active_config.model_dump()

    def update_config(self, patch: Dict[str, Any]) -> SystemConfig:
        """Apply partial update dictionary to active configuration with validation."""
        current_dict = self._active_config.model_dump()

        def deep_update(target: dict, source: dict):
            for k, v in source.items():
                if isinstance(v, dict) and k in target and isinstance(target[k], dict):
                    deep_update(target[k], v)
                else:
                    target[k] = v

        deep_update(current_dict, patch)
        validated = SystemConfig(**current_dict)
        self._active_config = validated
        return self._active_config

    def load_profile(self, profile_name: str) -> SystemConfig:
        """Load a preset configuration profile by name."""
        # Try YAML first
        yaml_path = self.config_dir / f"{profile_name}.yaml"
        if yaml_path.exists():
            data = load_yaml_file(yaml_path)
            self._active_config = SystemConfig(**data)
            return self._active_config

        # Try JSON
        json_path = self.config_dir / f"{profile_name}.json"
        if json_path.exists():
            data = load_json_file(json_path)
            self._active_config = SystemConfig(**data)
            return self._active_config

        raise FileNotFoundError(f"Configuration profile '{profile_name}' not found in {self.config_dir}")

    def save_profile(self, profile_name: str, as_yaml: bool = True) -> Path:
        """Save the active configuration as a new profile."""
        if as_yaml:
            out_path = self.config_dir / f"{profile_name}.yaml"
            save_yaml_file(out_path, self._active_config.model_dump())
        else:
            out_path = self.config_dir / f"{profile_name}.json"
            save_json_file(out_path, self._active_config.model_dump())
        return out_path

    def reset_to_default(self) -> SystemConfig:
        """Reset configuration to initial default values."""
        self._active_config = SystemConfig()
        return self._active_config
