"""
Repository interfaces for domain entities.

Following the Repository pattern, these define the contract
for data persistence without coupling to specific implementations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from .entities import Project, ContentSource, PDFSource, URLSource, Chapter, Script, Video
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
