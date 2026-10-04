"""Configuration file I/O utilities for YAML and JSON."""
import json
from pathlib import Path
from typing import Any, Dict
import yaml


def load_yaml_file(filepath: Path) -> Dict[str, Any]:
    """Load and parse YAML configuration file."""
    if not filepath.exists():
        raise FileNotFoundError(f"Configuration file not found: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}


def save_yaml_file(filepath: Path, data: Dict[str, Any]) -> None:
    """Save data dictionary to YAML file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)


def load_json_file(filepath: Path) -> Dict[str, Any]:
    """Load and parse JSON configuration file."""
    if not filepath.exists():
        raise FileNotFoundError(f"Configuration file not found: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json_file(filepath: Path, data: Dict[str, Any]) -> None:
    """Save data dictionary to JSON file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
