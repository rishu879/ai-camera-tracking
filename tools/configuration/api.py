"""FastAPI REST API for Configuration Manager."""
from typing import Any, Dict
from fastapi import FastAPI, HTTPException, Query
from tools.utilities.network import json_success_response, json_error_response
from .service import ConfigurationService

app = FastAPI(
    title="FSOC Configuration Manager API",
    description="Centralized configuration management service with YAML/JSON and profile switching.",
    version="1.0.0",
)

service = ConfigurationService()


@app.get("/health")
def health_check() -> Dict[str, Any]:
    return json_success_response({"status": "healthy", "service": "configuration_manager"})


@app.get("/config")
def get_configuration() -> Dict[str, Any]:
    """Retrieve full active system configuration."""
    return json_success_response(service.get_config_dict(), "Active configuration retrieved")


@app.post("/config")
def update_configuration(patch: Dict[str, Any]) -> Dict[str, Any]:
    """Update active configuration with partial dictionary."""
    try:
        updated = service.update_config(patch)
        return json_success_response(updated.model_dump(), "Configuration updated successfully")
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.get("/config/profiles")
def list_profiles() -> Dict[str, Any]:
    """List all available preset configuration profiles."""
    profiles = [p.stem for p in service.config_dir.glob("*.yaml")] + [
        p.stem for p in service.config_dir.glob("*.json")
    ]
    return json_success_response(list(set(profiles)), "Available profiles")


@app.post("/config/load_profile")
def load_profile(name: str = Query(..., description="Name of profile to load")) -> Dict[str, Any]:
    """Load configuration from a preset profile."""
    try:
        cfg = service.load_profile(name)
        return json_success_response(cfg.model_dump(), f"Profile '{name}' loaded successfully")
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/config/reset")
def reset_config() -> Dict[str, Any]:
    """Reset configuration to default settings."""
    cfg = service.reset_to_default()
    return json_success_response(cfg.model_dump(), "Configuration reset to default")
