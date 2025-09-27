"""
Application settings and configuration management.

Pydantic v2 compatible settings using pydantic-settings.
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Optional, List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .database import DatabaseConfig
from .providers import ProviderConfig


class Settings(BaseSettings):
    """
    Main application settings.
    
    Loads configuration from environment variables, .env files,
    and provides sensible defaults.
    """
    
    # Application
    app_name: str = Field("Paperclip", description="Application name")
    app_version: str = Field("0.1.0", description="Application version")
    debug: bool = Field(False, description="Debug mode")
    environment: str = Field("development", description="Environment (development/staging/production)")
    
    # API Server
    api_host: str = Field("0.0.0.0", description="API server host")
    api_port: int = Field(8000, description="API server port")
    api_workers: int = Field(1, description="Number of API workers")
    api_reload: bool = Field(True, description="Auto-reload API server")
    
    # UI Server
    ui_host: str = Field("0.0.0.0", description="UI server host")
    ui_port: int = Field(8501, description="UI server port")
    
    # Security
    secret_key: str = Field(..., description="Secret key for sessions and tokens")
    cors_origins: List[str] = Field(["*"], description="CORS allowed origins")
    
    # Database
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    
    # AI Providers
    providers: ProviderConfig = Field(default_factory=ProviderConfig)
    
    # File Storage
    upload_dir: Path = Field(Path("uploads"), description="Upload directory")
    output_dir: Path = Field(Path("output"), description="Output directory")
    temp_dir: Path = Field(Path("temp"), description="Temporary directory")
    max_upload_size: int = Field(100 * 1024 * 1024, description="Max upload size in bytes (100MB)")
    
    # Processing
    max_concurrent_jobs: int = Field(5, description="Max concurrent processing jobs")
    job_timeout: int = Field(3600, description="Job timeout in seconds (1 hour)")
    
    # Content Processing
    min_chapter_length: int = Field(300, description="Minimum chapter length in words")
    max_chapter_length: int = Field(2000, description="Maximum chapter length in words")
    default_script_template: str = Field("educational", description="Default script template")
    
    # Video Generation
    video_output_dir: Path = Field(Path("output/videos"), description="Video output directory")
    default_video_quality: str = Field("1080p", description="Default video quality")
    default_aspect_ratio: str = Field("16:9", description="Default aspect ratio")
    
    # Caching
    redis_url: str = Field("redis://localhost:6379/0", description="Redis URL for caching")
    cache_ttl: int = Field(3600, description="Default cache TTL in seconds")
    
    # Logging
    log_level: str = Field("INFO", description="Logging level")
    log_format: str = Field("json", description="Log format (json/text)")
    log_file: Optional[Path] = Field(None, description="Log file path")
    
    # Monitoring
    enable_metrics: bool = Field(True, description="Enable metrics collection")
    metrics_port: int = Field(9090, description="Metrics server port")
    
    @field_validator("upload_dir", "output_dir", "temp_dir", "video_output_dir", mode="before")
    def create_directories(cls, v):
        """Ensure directories exist."""
        if isinstance(v, str):
            v = Path(v)
        v.mkdir(parents=True, exist_ok=True)
        return v
    
    @field_validator("environment")
    def validate_environment(cls, v):
        """Validate environment value."""
        valid_envs = ["development", "staging", "production"]
        if v not in valid_envs:
            raise ValueError(f"Environment must be one of: {valid_envs}")
        return v
    
    @field_validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()
    
    @field_validator("cors_origins", mode="before")
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # pydantic-settings v2 configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
    )
    
    def get_database_url(self) -> str:
        """Get database connection URL."""
        return self.database.get_connection_url()
    
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"
    
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"
    
    def get_api_url(self) -> str:
        """Get API base URL."""
        return f"http://{self.api_host}:{self.api_port}"
    
    def get_ui_url(self) -> str:
        """Get UI base URL."""
        return f"http://{self.ui_host}:{self.ui_port}"


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings (cached).
    
    This function is cached to avoid re-parsing environment variables
    and configuration files on every access.
    """
    return Settings()


def create_example_env_file(path: str = ".env.example"):
    """Create an example .env file with all configuration options."""
    
    example_content = """# Paperclip Configuration
# Copy this file to .env and customize the values

# Application
APP_NAME=Paperclip
APP_VERSION=0.1.0
DEBUG=false
ENVIRONMENT=development

# API Server
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=1
API_RELOAD=true

# UI Server  
UI_HOST=0.0.0.0
UI_PORT=8501

# Security (REQUIRED)
SECRET_KEY=your-secret-key-here-change-this-in-production
CORS_ORIGINS=*

# Database (Supabase-compatible Postgres)
DATABASE__URL=postgresql://postgres:postgres@localhost:5433/paperclip

# AI Providers (at least one required)
PROVIDERS__OPENAI__API_KEY=your-openai-api-key
PROVIDERS__ANTHROPIC__API_KEY=your-anthropic-api-key

# Video Providers (optional)
PROVIDERS__RUNWAY__API_KEY=your-runway-api-key
PROVIDERS__PIKA__API_KEY=your-pika-api-key
PROVIDERS__LUMA__API_KEY=your-luma-api-key

# File Storage
UPLOAD_DIR=uploads
OUTPUT_DIR=output
TEMP_DIR=temp
MAX_UPLOAD_SIZE=104857600  # 100MB

# Processing
MAX_CONCURRENT_JOBS=5
JOB_TIMEOUT=3600
MIN_CHAPTER_LENGTH=300
MAX_CHAPTER_LENGTH=2000

# Video Generation
VIDEO_OUTPUT_DIR=output/videos
DEFAULT_VIDEO_QUALITY=1080p
DEFAULT_ASPECT_RATIO=16:9

# Caching
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=3600

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
# LOG_FILE=logs/paperclip.log

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
"""
    
    with open(path, 'w') as f:
        f.write(example_content.strip())
    
    print(f"Created example environment file: {path}")
    print("Copy this to .env and customize the values for your setup.")


if __name__ == "__main__":
    # Create example .env file when run directly
    create_example_env_file()
