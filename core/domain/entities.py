"""
Core domain entities for Paperclip.

Following Domain-Driven Design principles, these entities represent
the core business concepts with their behavior and invariants.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from dataclasses import dataclass, field

from .value_objects import (
    ProjectId, SourceId, ChapterId, ScriptId, VideoId,
    ContentMetadata, VideoConfig, ScriptConfig
)


class ProcessingStatus(str, Enum):
    """Status of content processing operations."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ContentType(str, Enum):
    """Types of content sources supported."""
    PDF = "pdf"
    URL = "url"


class VideoProvider(str, Enum):
    """Supported video generation providers."""
    RUNWAY = "runway"
    PIKA = "pika"
    LUMA = "luma"
    TEMPLATE = "template"  # Template-based generation
    CUSTOM = "custom"      # Custom rendering pipeline


class ScriptTemplate(str, Enum):
    """Video script templates for different content types."""
    EDUCATIONAL = "educational"
    DOCUMENTARY = "documentary"
    PRESENTATION = "presentation"
    TUTORIAL = "tutorial"
    SUMMARY = "summary"
    CUSTOM = "custom"


class JobType(str, Enum):
    """Types of processing jobs in the pipeline."""
    PARSE_DOCUMENT = "parse_document"
    GENERATE_SCRIPT = "generate_script"
    CREATE_VISUALS = "create_visuals"
    RENDER_VIDEO = "render_video"


class JobStatus(str, Enum):
    """Status of processing jobs."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TestMetric(str, Enum):
    """Metrics for A/B testing."""
    ENGAGEMENT = "engagement"
    COMPLETION = "completion"
    SHARES = "shares"


class ABTestStatus(str, Enum):
    """Status of A/B tests."""
    RUNNING = "running"
    COMPLETED = "completed"
    PAUSED = "paused"


class ProjectStatus(str, Enum):
    """Status of projects."""
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class FileType(str, Enum):
    """Types of files supported."""
    PDF = "pdf"
    TXT = "txt"
    DOCX = "docx"
    MD = "md"


class UploadStatus(str, Enum):
    """Status of document uploads."""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PARSED = "parsed"
    FAILED = "failed"


@dataclass
class Project:
    """
    A project represents a complete content-to-video transformation workflow.
    
    Similar to Open Notebook's notebook concept, but focused on video generation.
    """
    id: ProjectId
    name: str
    description: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    status: ProcessingStatus = ProcessingStatus.PENDING
    config: Dict[str, Any] = field(default_factory=dict)
    
    # Relationships
    sources: List["ContentSource"] = field(default_factory=list)
    chapters: List["Chapter"] = field(default_factory=list)
    scripts: List["Script"] = field(default_factory=list)
    videos: List["Video"] = field(default_factory=list)
    
    def add_source(self, source: "ContentSource") -> None:
        """Add a content source to this project."""
        if source not in self.sources:
            self.sources.append(source)
            self.updated_at = datetime.utcnow()
    
    def get_sources_by_type(self, content_type: ContentType) -> List["ContentSource"]:
        """Get all sources of a specific type."""
        return [s for s in self.sources if s.content_type == content_type]
    
    def mark_processing(self) -> None:
        """Mark project as currently processing."""
        self.status = ProcessingStatus.PROCESSING
        self.updated_at = datetime.utcnow()
    
    def mark_completed(self) -> None:
        """Mark project as completed."""
        self.status = ProcessingStatus.COMPLETED
        self.updated_at = datetime.utcnow()
    
    def mark_failed(self, error: str) -> None:
        """Mark project as failed with error details."""
        self.status = ProcessingStatus.FAILED
        self.config["last_error"] = error
        self.updated_at = datetime.utcnow()


@dataclass
class ContentSource:
    """
    Abstract base for content sources (PDF, URL, etc.).
    
    Inspired by Open Notebook's source handling but specialized for video generation.
    """
    id: SourceId
    project_id: ProjectId
    content_type: ContentType
    title: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    status: ProcessingStatus = ProcessingStatus.PENDING
    metadata: ContentMetadata = field(default_factory=lambda: ContentMetadata({}))
    
    # Processing results
    raw_content: Optional[str] = None
    processed_content: Optional[str] = None
    error_message: Optional[str] = None
    
    def mark_processing(self) -> None:
        """Mark source as currently being processed."""
        self.status = ProcessingStatus.PROCESSING
        self.updated_at = datetime.utcnow()
    
    def mark_completed(self, content: str) -> None:
        """Mark source processing as completed."""
        self.status = ProcessingStatus.COMPLETED
        self.processed_content = content
        self.updated_at = datetime.utcnow()
    
    def mark_failed(self, error: str) -> None:
        """Mark source processing as failed."""
        self.status = ProcessingStatus.FAILED
        self.error_message = error
        self.updated_at = datetime.utcnow()


@dataclass
class PDFSource(ContentSource):
    """
    PDF document source.
    
    Handles PDF-specific metadata and processing requirements.
    """
    file_path: str = ""
    file_size: Optional[int] = None
    page_count: Optional[int] = None
    
    def __post_init__(self):
        self.content_type = ContentType.PDF
    
    @property
    def display_name(self) -> str:
        """Get display name for this PDF source."""
        return self.title or self.file_path.split("/")[-1]


@dataclass 
class URLSource(ContentSource):
    """
    Web URL content source.
    
    Handles web scraping and URL-specific processing.
    """
    url: str = ""
    domain: Optional[str] = None
    scraped_at: Optional[datetime] = None
    
    def __post_init__(self):
        self.content_type = ContentType.URL
        if self.url:
            self.domain = self._extract_domain(self.url)
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        from urllib.parse import urlparse
        return urlparse(url).netloc
    
    @property
    def display_name(self) -> str:
        """Get display name for this URL source."""
        return self.title or self.url


@dataclass
class Chapter:
    """
    A logical chapter or section extracted from content.
    
    Represents a coherent unit of content that will become one video script.
    """
    id: ChapterId
    project_id: ProjectId
    source_id: SourceId
    title: str
    content: str
    order: int  # Chapter order within the source
    
    # Content analysis
    word_count: Optional[int] = None
    estimated_duration: Optional[float] = None  # in minutes
    key_topics: List[str] = field(default_factory=list)
    
    # Processing metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    status: ProcessingStatus = ProcessingStatus.PENDING
    
    def calculate_word_count(self) -> int:
        """Calculate and cache word count."""
        self.word_count = len(self.content.split())
        return self.word_count
    
    def estimate_duration(self, words_per_minute: int = 150) -> float:
        """Estimate video duration based on content length."""
        if not self.word_count:
            self.calculate_word_count()
        self.estimated_duration = (self.word_count or 0) / words_per_minute
        return self.estimated_duration


@dataclass
class Script:
    """
    Generated video script for a chapter.
    
    Contains the AI-generated script with metadata and configuration.
    """
    id: ScriptId
    project_id: ProjectId
    chapter_id: ChapterId
    title: str
    content: str
    
    # Script configuration
    template: ScriptTemplate = ScriptTemplate.EDUCATIONAL
    config: ScriptConfig = field(default_factory=lambda: ScriptConfig({}))
    
    # Generation metadata
    model_used: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    generation_time: Optional[float] = None  # in seconds
    
    # Processing status
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    status: ProcessingStatus = ProcessingStatus.PENDING
    
    # Estimated video properties
    estimated_duration: Optional[float] = None
    scene_count: Optional[int] = None
    
    def mark_generated(self, model: str, stats: Dict[str, Any]) -> None:
        """Mark script as successfully generated."""
        self.status = ProcessingStatus.COMPLETED
        self.model_used = model
        self.prompt_tokens = stats.get("prompt_tokens")
        self.completion_tokens = stats.get("completion_tokens")
        self.generation_time = stats.get("generation_time")
        self.updated_at = datetime.utcnow()


@dataclass
class Video:
    """
    Generated video from a script.
    
    Represents the final video output with metadata and provider information.
    """
    id: VideoId
    project_id: ProjectId
    script_id: ScriptId
    title: str
    
    # Video properties
    provider: VideoProvider
    config: VideoConfig = field(default_factory=lambda: VideoConfig({}))
    
    # File information
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    duration: Optional[float] = None  # in seconds
    resolution: Optional[str] = None  # e.g., "1920x1080"
    format: Optional[str] = None      # e.g., "mp4"
    
    # Generation metadata
    provider_job_id: Optional[str] = None
    generation_time: Optional[float] = None
    cost: Optional[float] = None
    
    # Processing status
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    status: ProcessingStatus = ProcessingStatus.PENDING
    error_message: Optional[str] = None
    
    def mark_generating(self, job_id: str) -> None:
        """Mark video as currently generating."""
        self.status = ProcessingStatus.PROCESSING
        self.provider_job_id = job_id
        self.updated_at = datetime.utcnow()
    
    def mark_completed(self, file_path: str, metadata: Dict[str, Any]) -> None:
        """Mark video generation as completed."""
        self.status = ProcessingStatus.COMPLETED
        self.file_path = file_path
        self.file_size = metadata.get("file_size")
        self.duration = metadata.get("duration")
        self.resolution = metadata.get("resolution")
        self.format = metadata.get("format")
        self.generation_time = metadata.get("generation_time")
        self.cost = metadata.get("cost")
        self.updated_at = datetime.utcnow()
    
    def mark_failed(self, error: str) -> None:
        """Mark video generation as failed."""
        self.status = ProcessingStatus.FAILED
        self.error_message = error
        self.updated_at = datetime.utcnow()
    
    @property
    def is_ready(self) -> bool:
        """Check if video is ready for viewing."""
        return (
            self.status == ProcessingStatus.COMPLETED
            and self.file_path is not None
        )


@dataclass
class ProcessingJob:
    """
    A processing job in the video generation pipeline.

    Tracks the execution of individual pipeline steps like document parsing,
    script generation, visual creation, and video rendering.
    """
    id: UUID
    project_id: ProjectId
    job_type: JobType
    status: JobStatus = JobStatus.QUEUED
    priority: int = 0
    progress: int = 0
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def mark_started(self) -> None:
        """Mark job as started processing."""
        self.status = JobStatus.PROCESSING
        self.started_at = datetime.utcnow()

    def mark_completed(self) -> None:
        """Mark job as completed."""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.progress = 100

    def mark_failed(self, error: str) -> None:
        """Mark job as failed with error message."""
        self.status = JobStatus.FAILED
        self.error_message = error
        self.completed_at = datetime.utcnow()

    def mark_cancelled(self) -> None:
        """Mark job as cancelled."""
        self.status = JobStatus.CANCELLED
        self.completed_at = datetime.utcnow()

    def update_progress(self, progress: int) -> None:
        """Update job progress (0-100)."""
        self.progress = max(0, min(100, progress))

    @property
    def is_active(self) -> bool:
        """Check if job is currently active."""
        return self.status in [JobStatus.QUEUED, JobStatus.PROCESSING]


@dataclass
class VideoAnalytics:
    """
    Analytics data for video performance.

    Tracks views and engagement metrics across different platforms.
    """
    id: UUID
    video_id: VideoId
    platform: str
    views: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)

    def increment_views(self, count: int = 1) -> None:
        """Increment view count."""
        self.views += count


@dataclass
class ABTest:
    """
    A/B test configuration for comparing video variants.

    Tests different video versions against specified metrics to determine
    which performs better for engagement, completion rates, or shares.
    """
    id: UUID
    project_id: ProjectId
    test_name: str
    variant_a_video_id: Optional[VideoId] = None
    variant_b_video_id: Optional[VideoId] = None
    test_metric: TestMetric = TestMetric.ENGAGEMENT
    sample_size: Optional[int] = None
    confidence_level: Optional[float] = None
    results: Optional[Dict[str, Any]] = None
    status: ABTestStatus = ABTestStatus.RUNNING
    created_at: datetime = field(default_factory=datetime.utcnow)

    def mark_completed(self, results: Dict[str, Any]) -> None:
        """Mark test as completed with results."""
        self.status = ABTestStatus.COMPLETED
        self.results = results

    def mark_paused(self) -> None:
        """Mark test as paused."""
        self.status = ABTestStatus.PAUSED

    def resume(self) -> None:
        """Resume a paused test."""
        if self.status == ABTestStatus.PAUSED:
            self.status = ABTestStatus.RUNNING

    @property
    def is_active(self) -> bool:
        """Check if test is currently active."""
        return self.status == ABTestStatus.RUNNING


@dataclass
class SimpleProject:
    """
    Simplified project entity for basic project management.

    Used for creating and managing projects with documents.
    """
    id: UUID
    name: str
    description: Optional[str] = None
    user_id: UUID
    status: ProjectStatus = ProjectStatus.PROCESSING
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Document:
    """
    Document entity for uploaded files.

    Represents files uploaded to a project (PDF, text, etc.).
    """
    id: UUID
    project_id: UUID
    filename: str
    file_type: FileType
    file_size: Optional[int] = None
    file_url: str
    upload_status: UploadStatus = UploadStatus.UPLOADED
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
