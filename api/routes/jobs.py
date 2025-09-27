"""
Processing jobs API endpoints.

Handles job management, status monitoring, and pipeline control.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Body
from pydantic import BaseModel, Field

from core.domain.entities import JobType, JobStatus, ProjectId
from ..dependencies import (
    CurrentUserDep,
    ProcessingJobServiceDep,  # Will need to add this
)

router = APIRouter()


# Request/Response models
class CreateJobRequest(BaseModel):
    """Request model for creating a processing job."""
    project_id: UUID = Field(..., description="Project ID")
    job_type: JobType = Field(..., description="Type of processing job")
    priority: int = Field(0, description="Job priority (higher = more important)")


class JobResponse(BaseModel):
    """Response model for job data."""
    id: str
    project_id: str
    job_type: JobType
    status: JobStatus
    priority: int
    progress: int
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime


class JobStatusResponse(BaseModel):
    """Response model for job status."""
    job_id: str
    status: JobStatus
    progress: int
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class PipelineStatusResponse(BaseModel):
    """Response model for pipeline status."""
    project_id: str
    total_jobs: int
    status_counts: Dict[str, int]
    active_jobs: int
    completed_jobs: int
    failed_jobs: int
    average_progress: float
    pipeline_progress: Dict[str, int]
    next_step: Optional[str] = None


@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    request: CreateJobRequest,
    current_user: CurrentUserDep,
    job_service: ProcessingJobServiceDep,
):
    """Create a new processing job."""
    job = await job_service.create_job(
        ProjectId(request.project_id),
        request.job_type,
        request.priority
    )

    return JobResponse(
        id=str(job.id),
        project_id=str(job.project_id),
        job_type=job.job_type,
        status=job.status,
        priority=job.priority,
        progress=job.progress,
        error_message=job.error_message,
        started_at=job.started_at,
        completed_at=job.completed_at,
        created_at=job.created_at
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: UUID,
    current_user: CurrentUserDep,
    job_service: ProcessingJobServiceDep,
):
    """Get a specific processing job."""
    job = await job_service.job_repo.get_by_id(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )

    return JobResponse(
        id=str(job.id),
        project_id=str(job.project_id),
        job_type=job.job_type,
        status=job.status,
        priority=job.priority,
        progress=job.progress,
        error_message=job.error_message,
        started_at=job.started_at,
        completed_at=job.completed_at,
        created_at=job.created_at
    )


@router.get("/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(
    job_id: UUID,
    current_user: CurrentUserDep,
    job_service: ProcessingJobServiceDep,
):
    """Get the status of a processing job."""
    job = await job_service.job_repo.get_by_id(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )

    return JobStatusResponse(
        job_id=str(job.id),
        status=job.status,
        progress=job.progress,
        error_message=job.error_message,
        started_at=job.started_at,
        completed_at=job.completed_at
    )


@router.post("/{job_id}/start")
async def start_job(
    job_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: CurrentUserDep,
    job_service: ProcessingJobServiceDep,
):
    """Start a queued processing job."""
    try:
        job = await job_service.start_job(job_id)

        # Add background task to process the job
        background_tasks.add_task(process_job_background, job_id, job_service)

        return {
            "job_id": str(job_id),
            "status": "started",
            "message": f"Job {job_id} has been started"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{job_id}/cancel")
async def cancel_job(
    job_id: UUID,
    current_user: CurrentUserDep,
    job_service: ProcessingJobServiceDep,
):
    """Cancel a processing job."""
    try:
        job = await job_service.cancel_job(job_id)
        return {
            "job_id": str(job_id),
            "status": "cancelled",
            "message": f"Job {job_id} has been cancelled"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/project/{project_id}", response_model=List[JobResponse])
async def list_project_jobs(
    project_id: UUID,
    current_user: CurrentUserDep,
    job_service: ProcessingJobServiceDep,
):
    """List all jobs for a project."""
    jobs = await job_service.get_project_jobs(ProjectId(project_id))

    return [JobResponse(
        id=str(job.id),
        project_id=str(job.project_id),
        job_type=job.job_type,
        status=job.status,
        priority=job.priority,
        progress=job.progress,
        error_message=job.error_message,
        started_at=job.started_at,
        completed_at=job.completed_at,
        created_at=job.created_at
    ) for job in jobs]


@router.get("/project/{project_id}/pipeline-status", response_model=PipelineStatusResponse)
async def get_pipeline_status(
    project_id: UUID,
    current_user: CurrentUserDep,
    job_service: ProcessingJobServiceDep,
):
    """Get the pipeline status for a project."""
    # This would need access to ProcessingPipeline
    # For now, return job summary
    summary = await job_service.get_job_status_summary(ProjectId(project_id))

    return PipelineStatusResponse(
        project_id=str(project_id),
        **summary,
        pipeline_progress={},  # Would need pipeline access
        next_step=None
    )


@router.post("/project/{project_id}/create-pipeline")
async def create_pipeline_jobs(
    project_id: UUID,
    current_user: CurrentUserDep,
    job_service: ProcessingJobServiceDep,
):
    """Create the standard pipeline jobs for a project."""
    jobs = await job_service.create_pipeline_jobs(ProjectId(project_id))

    return {
        "project_id": str(project_id),
        "jobs_created": len(jobs),
        "job_ids": [str(job.id) for job in jobs],
        "message": f"Created {len(jobs)} pipeline jobs for project {project_id}"
    }


@router.get("/queue/next")
async def get_next_queued_job(
    current_user: CurrentUserDep,
    job_service: ProcessingJobServiceDep,
):
    """Get the next job in the queue (for workers)."""
    job = await job_service.get_next_queued_job()

    if not job:
        return {"message": "No jobs in queue"}

    return {
        "job_id": str(job.id),
        "project_id": str(job.project_id),
        "job_type": job.job_type.value,
        "priority": job.priority,
        "created_at": job.created_at
    }


async def process_job_background(job_id: UUID, job_service: ProcessingJobServiceDep):
    """Background task to process a job."""
    # This would integrate with ProcessingPipeline
    # For now, just simulate processing
    import asyncio
    await asyncio.sleep(5)  # Simulate work

    # Mark as completed (in real implementation, this would be done by the pipeline)
    try:
        await job_service.complete_job(job_id)
    except Exception as e:
        await job_service.fail_job(job_id, str(e))