"""
Repository interfaces for domain entities.

Following the Repository pattern, these define the contract
for data persistence without coupling to specific implementations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from .entities import (
    Project, ContentSource, PDFSource, URLSource, Chapter, Script, Video,
    ProcessingJob, VideoAnalytics, ABTest, SimpleProject, Document
)
from .value_objects import ProjectId, SourceId, ChapterId, ScriptId, VideoId


class ProjectRepository(ABC):
    """Repository interface for Project entities."""
    
    @abstractmethod
    async def create(self, project: Project) -> Project:
        """Create a new project."""
        pass
    
    @abstractmethod
    async def get_by_id(self, project_id: ProjectId) -> Optional[Project]:
        """Get project by ID."""
        pass
    
    @abstractmethod
    async def get_all(self) -> List[Project]:
        """Get all projects."""
        pass
    
    @abstractmethod
    async def update(self, project: Project) -> Project:
        """Update an existing project."""
        pass
    
    @abstractmethod
    async def delete(self, project_id: ProjectId) -> None:
        """Delete a project."""
        pass
    
    @abstractmethod
    async def get_with_sources(self, project_id: ProjectId) -> Optional[Project]:
        """Get project with all its sources loaded."""
        pass


class ContentSourceRepository(ABC):
    """Repository interface for ContentSource entities."""
    
    @abstractmethod
    async def create(self, source: ContentSource) -> ContentSource:
        """Create a new content source."""
        pass
    
    @abstractmethod
    async def get_by_id(self, source_id: SourceId) -> Optional[ContentSource]:
        """Get source by ID."""
        pass
    
    @abstractmethod
    async def get_by_project_id(self, project_id: ProjectId) -> List[ContentSource]:
        """Get all sources for a project."""
        pass
    
    @abstractmethod
    async def update(self, source: ContentSource) -> ContentSource:
        """Update an existing source."""
        pass
    
    @abstractmethod
    async def delete(self, source_id: SourceId) -> None:
        """Delete a source."""
        pass
    
    @abstractmethod
    async def create_pdf_source(self, source: PDFSource) -> PDFSource:
        """Create a new PDF source."""
        pass
    
    @abstractmethod
    async def create_url_source(self, source: URLSource) -> URLSource:
        """Create a new URL source."""
        pass
    
    @abstractmethod
    async def get_pdf_sources(self, project_id: ProjectId) -> List[PDFSource]:
        """Get all PDF sources for a project."""
        pass
    
    @abstractmethod
    async def get_url_sources(self, project_id: ProjectId) -> List[URLSource]:
        """Get all URL sources for a project."""
        pass


class ChapterRepository(ABC):
    """Repository interface for Chapter entities."""
    
    @abstractmethod
    async def create(self, chapter: Chapter) -> Chapter:
        """Create a new chapter."""
        pass
    
    @abstractmethod
    async def get_by_id(self, chapter_id: ChapterId) -> Optional[Chapter]:
        """Get chapter by ID."""
        pass
    
    @abstractmethod
    async def get_by_source_id(self, source_id: SourceId) -> List[Chapter]:
        """Get all chapters for a source."""
        pass
    
    @abstractmethod
    async def get_by_project_id(self, project_id: ProjectId) -> List[Chapter]:
        """Get all chapters for a project."""
        pass
    
    @abstractmethod
    async def update(self, chapter: Chapter) -> Chapter:
        """Update an existing chapter."""
        pass
    
    @abstractmethod
    async def delete(self, chapter_id: ChapterId) -> None:
        """Delete a chapter."""
        pass
    
    @abstractmethod
    async def create_batch(self, chapters: List[Chapter]) -> List[Chapter]:
        """Create multiple chapters in a batch."""
        pass


class ScriptRepository(ABC):
    """Repository interface for Script entities."""
    
    @abstractmethod
    async def create(self, script: Script) -> Script:
        """Create a new script."""
        pass
    
    @abstractmethod
    async def get_by_id(self, script_id: ScriptId) -> Optional[Script]:
        """Get script by ID."""
        pass
    
    @abstractmethod
    async def get_by_chapter_id(self, chapter_id: ChapterId) -> Optional[Script]:
        """Get script for a specific chapter."""
        pass
    
    @abstractmethod
    async def get_by_project_id(self, project_id: ProjectId) -> List[Script]:
        """Get all scripts for a project."""
        pass
    
    @abstractmethod
    async def update(self, script: Script) -> Script:
        """Update an existing script."""
        pass
    
    @abstractmethod
    async def delete(self, script_id: ScriptId) -> None:
        """Delete a script."""
        pass
    
    @abstractmethod
    async def get_ready_for_video_generation(self) -> List[Script]:
        """Get scripts that are ready for video generation."""
        pass


class VideoRepository(ABC):
    """Repository interface for Video entities."""
    
    @abstractmethod
    async def create(self, video: Video) -> Video:
        """Create a new video."""
        pass
    
    @abstractmethod
    async def get_by_id(self, video_id: VideoId) -> Optional[Video]:
        """Get video by ID."""
        pass
    
    @abstractmethod
    async def get_by_script_id(self, script_id: ScriptId) -> Optional[Video]:
        """Get video for a specific script."""
        pass
    
    @abstractmethod
    async def get_by_project_id(self, project_id: ProjectId) -> List[Video]:
        """Get all videos for a project."""
        pass
    
    @abstractmethod
    async def update(self, video: Video) -> Video:
        """Update an existing video."""
        pass
    
    @abstractmethod
    async def delete(self, video_id: VideoId) -> None:
        """Delete a video."""
        pass
    
    @abstractmethod
    async def get_processing_videos(self) -> List[Video]:
        """Get videos that are currently being processed."""
        pass
    
    @abstractmethod
    async def get_completed_videos(self, project_id: ProjectId) -> List[Video]:
        """Get all completed videos for a project."""
        pass


class ProcessingJobRepository(ABC):
    """Repository interface for ProcessingJob entities."""

    @abstractmethod
    async def create(self, job: ProcessingJob) -> ProcessingJob:
        """Create a new processing job."""
        pass

    @abstractmethod
    async def get_by_id(self, job_id: UUID) -> Optional[ProcessingJob]:
        """Get job by ID."""
        pass

    @abstractmethod
    async def get_by_project_id(self, project_id: ProjectId) -> List[ProcessingJob]:
        """Get all jobs for a project."""
        pass

    @abstractmethod
    async def get_by_status(self, status: str) -> List[ProcessingJob]:
        """Get jobs by status."""
        pass

    @abstractmethod
    async def get_queued_jobs(self, limit: int = 50) -> List[ProcessingJob]:
        """Get queued jobs ordered by priority."""
        pass

    @abstractmethod
    async def update(self, job: ProcessingJob) -> ProcessingJob:
        """Update an existing job."""
        pass

    @abstractmethod
    async def delete(self, job_id: UUID) -> None:
        """Delete a job."""
        pass

    @abstractmethod
    async def get_active_jobs_for_project(self, project_id: ProjectId) -> List[ProcessingJob]:
        """Get active (queued/processing) jobs for a project."""
        pass


class VideoAnalyticsRepository(ABC):
    """Repository interface for VideoAnalytics entities."""

    @abstractmethod
    async def create(self, analytics: VideoAnalytics) -> VideoAnalytics:
        """Create a new analytics record."""
        pass

    @abstractmethod
    async def get_by_video_id(self, video_id: VideoId) -> List[VideoAnalytics]:
        """Get analytics for a specific video."""
        pass

    @abstractmethod
    async def get_by_platform(self, video_id: VideoId, platform: str) -> Optional[VideoAnalytics]:
        """Get analytics for a video on a specific platform."""
        pass

    @abstractmethod
    async def increment_views(self, video_id: VideoId, platform: str, count: int = 1) -> VideoAnalytics:
        """Increment view count for a video on a platform."""
        pass

    @abstractmethod
    async def get_total_views(self, video_id: VideoId) -> int:
        """Get total views across all platforms for a video."""
        pass

    @abstractmethod
    async def get_platform_stats(self, video_id: VideoId) -> Dict[str, int]:
        """Get view stats by platform for a video."""
        pass


class ABTestRepository(ABC):
    """Repository interface for ABTest entities."""

    @abstractmethod
    async def create(self, test: ABTest) -> ABTest:
        """Create a new A/B test."""
        pass

    @abstractmethod
    async def get_by_id(self, test_id: UUID) -> Optional[ABTest]:
        """Get test by ID."""
        pass

    @abstractmethod
    async def get_by_project_id(self, project_id: ProjectId) -> List[ABTest]:
        """Get all tests for a project."""
        pass

    @abstractmethod
    async def get_active_tests(self) -> List[ABTest]:
        """Get all active (running) tests."""
        pass

    @abstractmethod
    async def update(self, test: ABTest) -> ABTest:
        """Update an existing test."""
        pass

    @abstractmethod
    async def delete(self, test_id: UUID) -> None:
        """Delete a test."""
        pass

    @abstractmethod
    async def get_tests_by_video(self, video_id: VideoId) -> List[ABTest]:
        """Get all tests that include a specific video."""
        pass


class SimpleProjectRepository(ABC):
    """Repository interface for SimpleProject entities."""

    @abstractmethod
    async def create(self, project: SimpleProject) -> SimpleProject:
        """Create a new simple project."""
        pass

    @abstractmethod
    async def get_by_id(self, project_id: UUID) -> Optional[SimpleProject]:
        """Get project by ID."""
        pass

    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> List[SimpleProject]:
        """Get all projects for a user."""
        pass

    @abstractmethod
    async def update(self, project: SimpleProject) -> SimpleProject:
        """Update an existing project."""
        pass

    @abstractmethod
    async def delete(self, project_id: UUID) -> None:
        """Delete a project."""
        pass


class DocumentRepository(ABC):
    """Repository interface for Document entities."""

    @abstractmethod
    async def create(self, document: Document) -> Document:
        """Create a new document."""
        pass

    @abstractmethod
    async def get_by_id(self, document_id: UUID) -> Optional[Document]:
        """Get document by ID."""
        pass

    @abstractmethod
    async def get_by_project_id(self, project_id: UUID) -> List[Document]:
        """Get all documents for a project."""
        pass

    @abstractmethod
    async def update(self, document: Document) -> Document:
        """Update an existing document."""
        pass

    @abstractmethod
    async def delete(self, document_id: UUID) -> None:
        """Delete a document."""
        pass
