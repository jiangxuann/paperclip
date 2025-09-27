"""
Domain services for business logic.

Services orchestrate domain objects and repositories to implement
complex business operations.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import logging

from .domain.entities import ProcessingJob, JobType, JobStatus, ProjectId
from .domain.repositories import ProcessingJobRepository

logger = logging.getLogger(__name__)


class ProcessingJobService:
    """
    Service for managing processing job lifecycle.

    Handles job creation, status updates, queuing, and coordination
    of the video generation pipeline.
    """

    def __init__(self, job_repo: ProcessingJobRepository):
        self.job_repo = job_repo

    async def create_job(self, project_id: ProjectId, job_type: JobType,
                        priority: int = 0) -> ProcessingJob:
        """
        Create a new processing job.

        Args:
            project_id: Project the job belongs to
            job_type: Type of processing job
            priority: Job priority (higher = more important)

        Returns:
            Created ProcessingJob entity
        """
        job = ProcessingJob(
            id=UUID(),
            project_id=project_id,
            job_type=job_type,
            priority=priority
        )

        created_job = await self.job_repo.create(job)
        logger.info(f"Created processing job {created_job.id} for project {project_id}")
        return created_job

    async def start_job(self, job_id: UUID) -> ProcessingJob:
        """
        Mark a job as started.

        Args:
            job_id: Job to start

        Returns:
            Updated ProcessingJob entity
        """
        job = await self.job_repo.get_by_id(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        if job.status != JobStatus.QUEUED:
            raise ValueError(f"Job {job_id} is not in queued status")

        job.mark_started()
        updated_job = await self.job_repo.update(job)
        logger.info(f"Started processing job {job_id}")
        return updated_job

    async def update_job_progress(self, job_id: UUID, progress: int,
                                 message: Optional[str] = None) -> ProcessingJob:
        """
        Update job progress.

        Args:
            job_id: Job to update
            progress: Progress percentage (0-100)
            message: Optional status message

        Returns:
            Updated ProcessingJob entity
        """
        job = await self.job_repo.get_by_id(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        job.update_progress(progress)
        if message:
            job.error_message = message  # Use error_message for status updates

        updated_job = await self.job_repo.update(job)
        logger.debug(f"Updated job {job_id} progress to {progress}%")
        return updated_job

    async def complete_job(self, job_id: UUID) -> ProcessingJob:
        """
        Mark a job as completed.

        Args:
            job_id: Job to complete

        Returns:
            Updated ProcessingJob entity
        """
        job = await self.job_repo.get_by_id(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        job.mark_completed()
        updated_job = await self.job_repo.update(job)
        logger.info(f"Completed processing job {job_id}")
        return updated_job

    async def fail_job(self, job_id: UUID, error: str) -> ProcessingJob:
        """
        Mark a job as failed.

        Args:
            job_id: Job to fail
            error: Error message

        Returns:
            Updated ProcessingJob entity
        """
        job = await self.job_repo.get_by_id(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        job.mark_failed(error)
        updated_job = await self.job_repo.update(job)
        logger.error(f"Failed processing job {job_id}: {error}")
        return updated_job

    async def cancel_job(self, job_id: UUID) -> ProcessingJob:
        """
        Cancel a job.

        Args:
            job_id: Job to cancel

        Returns:
            Updated ProcessingJob entity
        """
        job = await self.job_repo.get_by_id(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        if job.status not in [JobStatus.QUEUED, JobStatus.PROCESSING]:
            raise ValueError(f"Job {job_id} cannot be cancelled (status: {job.status})")

        job.mark_cancelled()
        updated_job = await self.job_repo.update(job)
        logger.info(f"Cancelled processing job {job_id}")
        return updated_job

    async def get_next_queued_job(self) -> Optional[ProcessingJob]:
        """
        Get the next job to process based on priority and creation time.

        Returns:
            Next ProcessingJob to process, or None if no jobs queued
        """
        queued_jobs = await self.job_repo.get_queued_jobs(limit=1)
        return queued_jobs[0] if queued_jobs else None

    async def get_project_jobs(self, project_id: ProjectId) -> List[ProcessingJob]:
        """
        Get all jobs for a project.

        Args:
            project_id: Project ID

        Returns:
            List of ProcessingJob entities
        """
        return await self.job_repo.get_by_project_id(project_id)

    async def get_active_jobs(self, project_id: ProjectId) -> List[ProcessingJob]:
        """
        Get active (queued/processing) jobs for a project.

        Args:
            project_id: Project ID

        Returns:
            List of active ProcessingJob entities
        """
        return await self.job_repo.get_active_jobs_for_project(project_id)

    async def create_pipeline_jobs(self, project_id: ProjectId) -> List[ProcessingJob]:
        """
        Create the standard pipeline jobs for a project.

        Creates jobs for: parse_document, generate_script, create_visuals, render_video

        Args:
            project_id: Project ID

        Returns:
            List of created ProcessingJob entities
        """
        job_types = [
            (JobType.PARSE_DOCUMENT, 10),  # High priority
            (JobType.GENERATE_SCRIPT, 8),
            (JobType.CREATE_VISUALS, 6),
            (JobType.RENDER_VIDEO, 4),    # Lower priority
        ]

        jobs = []
        for job_type, priority in job_types:
            job = await self.create_job(project_id, job_type, priority)
            jobs.append(job)

        logger.info(f"Created pipeline jobs for project {project_id}: {[j.id for j in jobs]}")
        return jobs

    async def get_job_status_summary(self, project_id: ProjectId) -> Dict[str, Any]:
        """
        Get a summary of job statuses for a project.

        Args:
            project_id: Project ID

        Returns:
            Dictionary with status counts and details
        """
        jobs = await self.get_project_jobs(project_id)

        status_counts = {}
        for job in jobs:
            status = job.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        active_jobs = [j for j in jobs if j.is_active]

        return {
            "total_jobs": len(jobs),
            "status_counts": status_counts,
            "active_jobs": len(active_jobs),
            "completed_jobs": status_counts.get("completed", 0),
            "failed_jobs": status_counts.get("failed", 0),
            "average_progress": sum(j.progress for j in jobs) / len(jobs) if jobs else 0,
        }