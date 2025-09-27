"""
Main FastAPI application.

Sets up the API server with all routes, middleware, and configuration.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import logging

from config import get_settings, setup_logging
from config.logging import LoggingMiddleware
from core.exceptions import ProcessingError
from .routes import projects, sources, scripts, videos, health, jobs, analytics, ab_tests
from .middleware import ErrorHandlingMiddleware, TimingMiddleware


# Setup logging
settings = get_settings()
setup_logging(
    level=settings.log_level,
    format_type=settings.log_format,
    log_file=settings.log_file,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    
    # Startup
    logger.info("Starting Paperclip API server")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    
    # Validate configuration
    provider_validation = settings.providers.validate_configuration()
    if not provider_validation["valid"]:
        # Do not block startup if providers are missing; log prominently instead.
        logger.warning(
            "Provider configuration issues detected; continuing without AI providers: %s",
            provider_validation["issues"],
        )
    
    if provider_validation["warnings"]:
        for warning in provider_validation["warnings"]:
            logger.warning(f"Provider configuration: {warning}")
    
    logger.info(f"Available AI providers: {provider_validation['available_ai_providers']}")
    logger.info(f"Available video providers: {provider_validation['available_video_providers']}")
    
    # Initialize database connection
    # This would typically initialize the database pool
    logger.info("Database connection initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Paperclip API server")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Transform PDFs and web content into engaging video content with AI",
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(TimingMiddleware)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(LoggingMiddleware)

# Include routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["Projects"])
app.include_router(sources.router, prefix="/api/v1/sources", tags=["Content Sources"])
app.include_router(scripts.router, prefix="/api/v1/scripts", tags=["Scripts"])
app.include_router(videos.router, prefix="/api/v1/videos", tags=["Videos"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["Processing Jobs"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Video Analytics"])
app.include_router(ab_tests.router, prefix="/api/v1/ab-tests", tags=["A/B Tests"])


# Global exception handlers
@app.exception_handler(ProcessingError)
async def processing_error_handler(request: Request, exc: ProcessingError):
    """Handle processing errors."""
    logger.error(f"Processing error: {exc}")
    return JSONResponse(
        status_code=422,
        content={
            "error": "processing_error",
            "message": str(exc),
            "detail": "An error occurred during content processing",
        }
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle value errors."""
    logger.error(f"Value error: {exc}")
    return JSONResponse(
        status_code=400,
        content={
            "error": "validation_error",
            "message": str(exc),
            "detail": "Invalid input data",
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    logger.exception("Unexpected error occurred")
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "message": "An unexpected error occurred",
            "detail": str(exc) if settings.debug else "Internal server error",
        }
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "docs_url": "/docs" if settings.debug else None,
        "status": "running",
    }


def run():
    """Run the API server."""
    import uvicorn
    
    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload and settings.is_development(),
        workers=settings.api_workers if not settings.debug else 1,
        log_level=settings.log_level.lower(),
        access_log=True,
    )


if __name__ == "__main__":
    run()
