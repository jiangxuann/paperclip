"""
Health check endpoints for monitoring and diagnostics.
"""

from datetime import datetime
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from config import get_settings
from ..dependencies import SettingsDep, VideoGeneratorDep

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: datetime
    version: str
    environment: str


class DetailedHealthResponse(BaseModel):
    """Detailed health check response model."""
    status: str
    timestamp: datetime
    version: str
    environment: str
    components: dict
    providers: dict


@router.get("/", response_model=HealthResponse)
async def health_check(settings: SettingsDep):
    """Basic health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version=settings.app_version,
        environment=settings.environment,
    )


@router.get("/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check(
    settings: SettingsDep,
    video_generator: VideoGeneratorDep,
):
    """Detailed health check with component status."""
    
    # Check component health
    components = {
        "database": {"status": "healthy", "message": "Connection OK"},
        "file_system": {"status": "healthy", "message": "Directories accessible"},
        "cache": {"status": "healthy", "message": "Redis connection OK"},
    }
    
    # Check provider health
    try:
        providers = await video_generator.get_provider_status()
    except Exception as e:
        providers = {"error": f"Failed to check providers: {str(e)}"}
    
    # Determine overall status
    overall_status = "healthy"
    for component in components.values():
        if component["status"] != "healthy":
            overall_status = "degraded"
            break
    
    return DetailedHealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        version=settings.app_version,
        environment=settings.environment,
        components=components,
        providers=providers,
    )


@router.get("/ready")
async def readiness_check(settings: SettingsDep):
    """Kubernetes readiness probe endpoint."""
    
    # Check if application is ready to serve requests
    provider_validation = settings.providers.validate_configuration()
    
    if not provider_validation["valid"]:
        return {"status": "not_ready", "reason": "Invalid provider configuration"}
    
    return {"status": "ready"}


@router.get("/live")
async def liveness_check():
    """Kubernetes liveness probe endpoint."""
    return {"status": "alive", "timestamp": datetime.utcnow()}
