"""Configuration for Structured Logging Service."""
from pathlib import Path
from pydantic import BaseModel, Field


class LoggingConfig(BaseModel):
    log_dir: str = Field(default="outputs/logs", description="Directory where log files are stored")
    max_bytes: int = Field(default=10 * 1024 * 1024, description="Max log file size in bytes before rotation (10MB)")
    backup_count: int = Field(default=5, description="Number of rotated backup log files to retain")
    log_level: str = Field(default="INFO", description="Default log level: DEBUG, INFO, WARNING, ERROR")
    console_output: bool = Field(default=True, description="Also emit formatted logs to standard stdout")
