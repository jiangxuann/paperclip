"""
Processing pipeline orchestrator.

Coordinates the end-to-end processing of content sources into videos,
managing job queues and dependencies between processing steps.
"""

import asyncio
from typing import List, Optional, Dict, Any
import logging
from uuid import UUID

from core.domain.entities import (
    Project, ContentSource, Chapter, Script, Video,
    ProcessingJob, JobType, JobStatus, ProjectId
)
from core.services import ProcessingJobService
from .content import ContentAnalyzer, ChapterExtractor
from .script import ScriptGenerator
from .pdf.structured_processor import StructuredPDFProcessor
from .url import URLProcessor
from .text import TextProcessor
from generators.video import VideoGenerator
from db.repositories import (
    PostgresDocumentPageRepository, PostgresContentBlockRepository,
    PostgresMediaAssetRepository, PostgresExtractedEntityRepository
)

logger = logging.getLogger(__name__)


class ProcessingPipeline:
    """
    Orchestrates the complete content-to-video processing pipeline.

    Manages the sequence: parse_document -> generate_script -> create_visuals -> render_video
    with proper job tracking and error handling.
    """

    def __init__(self, job_service: ProcessingJobService,
                 content_analyzer: ContentAnalyzer,
                 chapter_extractor: ChapterExtractor,
                 script_generator: ScriptGenerator,
                 video_generator: VideoGenerator,
                 db_connection=None):
        """
        Initialize the processing pipeline.

        Args:
            job_service: Service for managing processing jobs
            content_analyzer: Service for analyzing content
            chapter_extractor: Service for extracting chapters
            script_generator: Service for generating scripts
            video_generator: Service for generating videos
            db_connection: Database connection for structured processors
        """
        self.job_service = job_service
        self.content_analyzer = content_analyzer
        self.chapter_extractor = chapter_extractor
        self.script_generator = script_generator
        self.video_generator = video_generator
        self.db_connection = db_connection

        # Initialize structured processors if database is available
        if db_connection:
            from db.repositories import (
                PostgresDocumentPageRepository, PostgresContentBlockRepository,
                PostgresMediaAssetRepository, PostgresExtractedEntityRepository
            )
            self.page_repo = PostgresDocumentPageRepository(db_connection)
            self.content_repo = PostgresContentBlockRepository(db_connection)
            self.media_repo = PostgresMediaAssetRepository(db_connection)
            self.entity_repo = PostgresExtractedEntityRepository(db_connection)

            from .pdf.structured_processor import StructuredPDFProcessor
            from .text import TextProcessor
            self.pdf_processor = StructuredPDFProcessor(
                self.page_repo, self.content_repo, self.media_repo, self.entity_repo
            )
            self.text_processor = TextProcessor(
                self.page_repo, self.content_repo, self.media_repo, self.entity_repo
            )
        else:
            # Fallback to basic processors
            from .pdf import PDFProcessor
            from .url import URLProcessor
            self.pdf_processor = PDFProcessor()
            self.text_processor = None

        from .url import URLProcessor
        self.url_processor = URLProcessor()

    async def process_project(self, project: Project) -> None:
        """
        Process an entire project through the pipeline.

        Args:
            project: Project to process
        """
        logger.info(f"Starting pipeline processing for project {project.id}")

        try:
            # Create pipeline jobs
            jobs = await self.job_service.create_pipeline_jobs(project.id)

            # Process sources
            await self._process_sources(project)

            # Extract chapters
            chapters = await self._extract_chapters(project)

            # Generate scripts
            scripts = await self._generate_scripts(project, chapters)

            # Generate videos
            videos = await self._generate_videos(project, scripts)

            logger.info(f"Completed pipeline processing for project {project.id}")

        except Exception as e:
            logger.error(f"Pipeline processing failed for project {project.id}: {str(e)}")
            # Mark project as failed
            project.mark_failed(str(e))
            raise

    async def _process_sources(self, project: Project) -> None:
        """
        Process all content sources for a project.

        Args:
            project: Project containing sources to process
        """
        logger.info(f"Processing {len(project.sources)} sources for project {project.id}")

        for source in project.sources:
            try:
                # Create and start parse job
                job = await self.job_service.create_job(project.id, JobType.PARSE_DOCUMENT, 10)
                await self.job_service.start_job(job.id)

                # Process based on source type
                if source.content_type.value == "pdf":
                    processed_source = await self.pdf_processor.process(source)
                    processed_content = processed_source.processed_content
                elif source.content_type.value == "url":
                    processed_source = await self.url_processor.process_url(source)
                    processed_content = processed_source.processed_content
                elif source.content_type.value == "text":
                    if self.text_processor:
                        processed_source = await self.text_processor.process_text(source)
                        processed_content = processed_source.processed_content
                    else:
                        raise ValueError("Text processor not available")
                else:
                    raise ValueError(f"Unsupported content type: {source.content_type}")

                # Update source with processed content
                source.mark_completed(processed_content)
                await self.job_service.complete_job(job.id)

            except Exception as e:
                error_msg = f"Failed to process source {source.id}: {str(e)}"
                logger.error(error_msg)
                source.mark_failed(error_msg)
                await self.job_service.fail_job(job.id, error_msg)
                raise

    async def _extract_chapters(self, project: Project) -> List[Chapter]:
        """
        Extract chapters from processed content sources.

        Args:
            project: Project to extract chapters for

        Returns:
            List of extracted chapters
        """
        logger.info(f"Extracting chapters for project {project.id}")

        chapters = []
        for source in project.sources:
            if not source.processed_content:
                continue

            try:
                # Analyze content
                analysis = await self.content_analyzer.analyze(source.processed_content)

                # Extract chapters
                source_chapters = await self.chapter_extractor.extract_chapters(
                    source.processed_content, analysis
                )

                chapters.extend(source_chapters)

            except Exception as e:
                logger.error(f"Failed to extract chapters from source {source.id}: {str(e)}")
                raise

        logger.info(f"Extracted {len(chapters)} chapters for project {project.id}")
        return chapters

    async def _generate_scripts(self, project: Project, chapters: List[Chapter]) -> List[Script]:
        """
        Generate video scripts from chapters.

        Args:
            project: Project to generate scripts for
            chapters: Chapters to generate scripts from

        Returns:
            List of generated scripts
        """
        logger.info(f"Generating scripts for {len(chapters)} chapters in project {project.id}")

        scripts = []
        for chapter in chapters:
            try:
                # Create and start script generation job
                job = await self.job_service.create_job(project.id, JobType.GENERATE_SCRIPT, 8)
                await self.job_service.start_job(job.id)

                # Generate script
                script = await self.script_generator.generate_script(chapter)

                scripts.append(script)
                await self.job_service.complete_job(job.id)

            except Exception as e:
                error_msg = f"Failed to generate script for chapter {chapter.id}: {str(e)}"
                logger.error(error_msg)
                await self.job_service.fail_job(job.id, error_msg)
                raise

        logger.info(f"Generated {len(scripts)} scripts for project {project.id}")
        return scripts

    async def _generate_videos(self, project: Project, scripts: List[Script]) -> List[Video]:
        """
        Generate videos from scripts.

        Args:
            project: Project to generate videos for
            scripts: Scripts to generate videos from

        Returns:
            List of generated videos
        """
        logger.info(f"Generating videos for {len(scripts)} scripts in project {project.id}")

        videos = []
        for script in scripts:
            try:
                # Create and start video generation jobs
                visuals_job = await self.job_service.create_job(project.id, JobType.CREATE_VISUALS, 6)
                render_job = await self.job_service.create_job(project.id, JobType.RENDER_VIDEO, 4)

                # Start visuals job
                await self.job_service.start_job(visuals_job.id)

                # Generate video (this handles both visuals and rendering)
                video = await self.video_generator.generate_video(script)

                videos.append(video)

                # Complete jobs
                await self.job_service.complete_job(visuals_job.id)
                await self.job_service.complete_job(render_job.id)

            except Exception as e:
                error_msg = f"Failed to generate video for script {script.id}: {str(e)}"
                logger.error(error_msg)
                # Note: video generation jobs would need to be failed here
                raise

        logger.info(f"Generated {len(videos)} videos for project {project.id}")
        return videos

    async def process_job(self, job: ProcessingJob) -> None:
        """
        Process a single job based on its type.

        Args:
            job: Job to process
        """
        logger.info(f"Processing job {job.id} of type {job.job_type.value}")

        try:
            await self.job_service.start_job(job.id)

            if job.job_type == JobType.PARSE_DOCUMENT:
                await self._process_parse_job(job)
            elif job.job_type == JobType.GENERATE_SCRIPT:
                await self._process_script_job(job)
            elif job.job_type == JobType.CREATE_VISUALS:
                await self._process_visuals_job(job)
            elif job.job_type == JobType.RENDER_VIDEO:
                await self._process_render_job(job)
            else:
                raise ValueError(f"Unknown job type: {job.job_type}")

            await self.job_service.complete_job(job.id)

        except Exception as e:
            error_msg = f"Job {job.id} failed: {str(e)}"
            logger.error(error_msg)
            await self.job_service.fail_job(job.id, error_msg)
            raise

    async def _process_parse_job(self, job: ProcessingJob) -> None:
        """Process a document parsing job."""
        # Implementation would depend on having access to the specific source
        # This is a placeholder - actual implementation would need source repository
        logger.info(f"Processing parse job {job.id}")
        await asyncio.sleep(1)  # Simulate processing

    async def _process_script_job(self, job: ProcessingJob) -> None:
        """Process a script generation job."""
        logger.info(f"Processing script job {job.id}")
        await asyncio.sleep(1)  # Simulate processing

    async def _process_visuals_job(self, job: ProcessingJob) -> None:
        """Process a visuals creation job."""
        logger.info(f"Processing visuals job {job.id}")
        await asyncio.sleep(1)  # Simulate processing

    async def _process_render_job(self, job: ProcessingJob) -> None:
        """Process a video rendering job."""
        logger.info(f"Processing render job {job.id}")
        await asyncio.sleep(1)  # Simulate processing

    async def get_pipeline_status(self, project_id: ProjectId) -> Dict[str, Any]:
        """
        Get the current status of the processing pipeline for a project.

        Args:
            project_id: Project ID

        Returns:
            Dictionary with pipeline status information
        """
        status_summary = await self.job_service.get_job_status_summary(project_id)

        # Add pipeline-specific information
        job_progress = {
            JobType.PARSE_DOCUMENT.value: 0,
            JobType.GENERATE_SCRIPT.value: 0,
            JobType.CREATE_VISUALS.value: 0,
            JobType.RENDER_VIDEO.value: 0,
        }

        jobs = await self.job_service.get_project_jobs(project_id)
        for job in jobs:
            job_progress[job.job_type.value] = max(
                job_progress[job.job_type.value], job.progress
            )

        return {
            **status_summary,
            "pipeline_progress": job_progress,
            "next_step": self._determine_next_step(job_progress),
        }

    def _determine_next_step(self, job_progress: Dict[str, int]) -> Optional[str]:
        """Determine the next step in the pipeline based on current progress."""
        if job_progress[JobType.PARSE_DOCUMENT.value] < 100:
            return "parsing_documents"
        elif job_progress[JobType.GENERATE_SCRIPT.value] < 100:
            return "generating_scripts"
        elif job_progress[JobType.CREATE_VISUALS.value] < 100:
            return "creating_visuals"
        elif job_progress[JobType.RENDER_VIDEO.value] < 100:
            return "rendering_videos"
        else:
            return None