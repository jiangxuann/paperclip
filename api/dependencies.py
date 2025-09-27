"""
FastAPI dependencies for dependency injection.

Provides reusable dependencies for database connections,
authentication, configuration, and service instances.
"""

from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config import Settings, get_settings


# Security
security = HTTPBearer(auto_error=False)


async def get_database():
    """
    Get database connection.

    Provides a database connection instance for repositories.
    """
    from config import get_settings
    from db.repositories import DatabaseConnection

    settings = get_settings()
    db_config = settings.database

    # Create database connection
    db = DatabaseConnection(db_config.url)
    await db.connect()
    return db


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)] = None
):
    """
    Get current authenticated user.
    
    For now, this is a placeholder. In production, you'd validate
    the JWT token and return user information.
    """
    # For development, allow unauthenticated access
    settings = get_settings()
    if settings.is_development():
        return {"id": "dev-user", "email": "dev@paperclip.ai", "role": "admin"}
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # TODO: Validate JWT token
    # For now, return a placeholder user
    return {"id": "user-123", "email": "user@example.com", "role": "user"}


async def get_admin_user(current_user: dict = Depends(get_current_user)):
    """Require admin user."""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


# Service dependencies
async def get_pdf_processor():
    """Get PDF processor instance."""
    from processors.pdf import PDFProcessor
    return PDFProcessor()


async def get_url_processor():
    """Get URL processor instance."""
    from processors.url import URLProcessor
    return URLProcessor()


async def get_content_analyzer():
    """Get content analyzer instance."""
    from processors.content import ContentAnalyzer
    # TODO: Initialize with AI client
    return ContentAnalyzer()


async def get_chapter_extractor():
    """Get chapter extractor instance."""
    from processors.content import ChapterExtractor
    # TODO: Initialize with AI client
    return ChapterExtractor()


async def get_script_generator():
    """Get script generator instance."""
    from processors.script import ScriptGenerator
    # TODO: Initialize with AI client
    return ScriptGenerator()


async def get_video_generator():
    """Get video generator instance."""
    from generators.video import VideoGenerator
    settings = get_settings()
    
    # Build provider configuration
    provider_config = {
        "providers": {
            "runway": {
                "api_key": settings.providers.runway.api_key,
                **settings.providers.runway.model_dump(),
            },
            "pika": {
                "api_key": settings.providers.pika.api_key,
                **settings.providers.pika.model_dump(),
            },
            "luma": {
                "api_key": settings.providers.luma.api_key,
                **settings.providers.luma.model_dump(),
            },
            "template": settings.providers.template.model_dump(),
        },
        "output_dir": str(settings.video_output_dir),
    }
    
    return VideoGenerator(config=provider_config)


# Repository dependencies
async def get_simple_project_repository():
    """Get simple project repository instance."""
    from db.repositories import PostgresSimpleProjectRepository
    db = await get_database()
    return PostgresSimpleProjectRepository(db)


async def get_document_repository():
    """Get document repository instance."""
    from db.repositories import PostgresDocumentRepository
    db = await get_database()
    return PostgresDocumentRepository(db)


async def get_source_repository():
    """Get content source repository instance."""
    # TODO: Implement actual repository
    return {"type": "source_repository", "status": "placeholder"}


async def get_chapter_repository():
    """Get chapter repository instance."""
    # TODO: Implement actual repository
    return {"type": "chapter_repository", "status": "placeholder"}


async def get_script_repository():
    """Get script repository instance."""
    # TODO: Implement actual repository
    return {"type": "script_repository", "status": "placeholder"}


async def get_video_repository():
    """Get video repository instance."""
    # TODO: Implement actual repository
    return {"type": "video_repository", "status": "placeholder"}


# Common type annotations for dependency injection
SettingsDep = Annotated[Settings, Depends(get_settings)]
DatabaseDep = Annotated[dict, Depends(get_database)]
CurrentUserDep = Annotated[dict, Depends(get_current_user)]
AdminUserDep = Annotated[dict, Depends(get_admin_user)]

# Processor dependencies
PDFProcessorDep = Annotated[object, Depends(get_pdf_processor)]
URLProcessorDep = Annotated[object, Depends(get_url_processor)]
ContentAnalyzerDep = Annotated[object, Depends(get_content_analyzer)]
ChapterExtractorDep = Annotated[object, Depends(get_chapter_extractor)]
ScriptGeneratorDep = Annotated[object, Depends(get_script_generator)]
VideoGeneratorDep = Annotated[object, Depends(get_video_generator)]

# Repository dependencies
SimpleProjectRepositoryDep = Annotated[object, Depends(get_simple_project_repository)]
DocumentRepositoryDep = Annotated[object, Depends(get_document_repository)]
ProjectRepositoryDep = Annotated[dict, Depends(get_project_repository)]
SourceRepositoryDep = Annotated[dict, Depends(get_source_repository)]
ChapterRepositoryDep = Annotated[dict, Depends(get_chapter_repository)]
ScriptRepositoryDep = Annotated[dict, Depends(get_script_repository)]
VideoRepositoryDep = Annotated[dict, Depends(get_video_repository)]

# New repository dependencies (placeholder for actual implementations)
async def get_processing_job_repository():
    """Get processing job repository instance."""
    # TODO: Implement actual repository
    return {"type": "processing_job_repository", "status": "placeholder"}

async def get_video_analytics_repository():
    """Get video analytics repository instance."""
    # TODO: Implement actual repository
    return {"type": "video_analytics_repository", "status": "placeholder"}

async def get_ab_test_repository():
    """Get A/B test repository instance."""
    # TODO: Implement actual repository
    return {"type": "ab_test_repository", "status": "placeholder"}

# New service dependencies
async def get_processing_job_service():
    """Get processing job service instance."""
    from core.services import ProcessingJobService
    # TODO: Initialize with actual repository
    job_repo = await get_processing_job_repository()
    return ProcessingJobService(job_repo)

async def get_ab_test_service():
    """Get A/B test service instance."""
    from core.ab_test_service import ABTestService
    # TODO: Initialize with actual repositories
    ab_test_repo = await get_ab_test_repository()
    analytics_repo = await get_video_analytics_repository()
    return ABTestService(ab_test_repo, analytics_repo)

# New repository dependencies
ProcessingJobRepositoryDep = Annotated[dict, Depends(get_processing_job_repository)]
VideoAnalyticsRepositoryDep = Annotated[dict, Depends(get_video_analytics_repository)]
ABTestRepositoryDep = Annotated[dict, Depends(get_ab_test_repository)]
ProcessingJobServiceDep = Annotated[object, Depends(get_processing_job_service)]
ABTestServiceDep = Annotated[object, Depends(get_ab_test_service)]
