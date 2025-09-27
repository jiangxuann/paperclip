"""
Core domain models for Paperclip.

This module contains the core business entities and domain logic
for the PDF and URL to video transformation pipeline.
"""

from .entities import (
    Project,
    ContentSource,
    PDFSource,
    URLSource,
    Chapter,
    Script,
    Video,
    ProcessingStatus,
    ContentType,
    VideoProvider,
    ScriptTemplate,
    SimpleProject,
    Document,
    ProjectStatus,
    FileType,
    UploadStatus
)

from .value_objects import (
    ProjectId,
    SourceId,
    ChapterId,
    ScriptId,
    VideoId,
    ContentMetadata,
    VideoConfig,
    ScriptConfig
)

from .repositories import (
    ProjectRepository,
    ContentSourceRepository,
    ChapterRepository,
    ScriptRepository,
    VideoRepository,
    SimpleProjectRepository,
    DocumentRepository
)

__all__ = [
    # Entities
    "Project",
    "ContentSource",
    "PDFSource",
    "URLSource",
    "Chapter",
    "Script",
    "Video",
    "ProcessingStatus",
    "ContentType",
    "VideoProvider",
    "ScriptTemplate",
    "SimpleProject",
    "Document",
    "ProjectStatus",
    "FileType",
    "UploadStatus",

    # Value Objects
    "ProjectId",
    "SourceId",
    "ChapterId",
    "ScriptId",
    "VideoId",
    "ContentMetadata",
    "VideoConfig",
    "ScriptConfig",

    # Repositories
    "ProjectRepository",
    "ContentSourceRepository",
    "ChapterRepository",
    "ScriptRepository",
    "VideoRepository",
    "SimpleProjectRepository",
    "DocumentRepository",
]
