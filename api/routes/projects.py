"""
Project management API endpoints.

Handles CRUD operations for projects and project-level operations.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from core.domain import SimpleProject, ProjectStatus
from ..dependencies import (
    CurrentUserDep,
    SimpleProjectRepositoryDep,
    DocumentRepositoryDep,
)

router = APIRouter()


# Request/Response models
class CreateProjectRequest(BaseModel):
    """Request model for creating a new project."""
    name: str = Field(..., min_length=1, max_length=200, description="Project name")
    description: Optional[str] = Field(None, max_length=1000, description="Project description")


class UpdateProjectRequest(BaseModel):
    """Request model for updating a project."""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Project name")
    description: Optional[str] = Field(None, max_length=1000, description="Project description")


class ProjectResponse(BaseModel):
    """Response model for project data."""
    id: str
    name: str
    description: Optional[str]
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime
    user_id: str

    # Statistics
    document_count: int = 0


class ProjectDetailResponse(ProjectResponse):
    """Detailed project response with related entities."""
    sources: List[dict] = Field(default_factory=list)
    recent_activity: List[dict] = Field(default_factory=list)


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    request: CreateProjectRequest,
    current_user: CurrentUserDep,
    project_repo: SimpleProjectRepositoryDep,
):
    """Create a new project."""

    from uuid import uuid4

    # Create project entity
    project = SimpleProject(
        id=uuid4(),
        name=request.name,
        description=request.description,
        user_id=current_user["id"],
    )

    # Save to database
    project = await project_repo.create(project)

    return ProjectResponse(
        id=str(project.id),
        name=project.name,
        description=project.description,
        status=project.status,
        created_at=project.created_at,
        updated_at=project.updated_at,
        user_id=str(project.user_id),
    )


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    current_user: CurrentUserDep,
    project_repo: SimpleProjectRepositoryDep,
    skip: int = 0,
    limit: int = 20,
):
    """List all projects for the current user."""

    from uuid import UUID

    # Get projects for user
    projects = await project_repo.get_by_user_id(UUID(current_user["id"]))

    return [ProjectResponse(
        id=str(p.id),
        name=p.name,
        description=p.description,
        status=p.status,
        created_at=p.created_at,
        updated_at=p.updated_at,
        user_id=str(p.user_id),
    ) for p in projects]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    current_user: CurrentUserDep,
    project_repo: SimpleProjectRepositoryDep,
    document_repo: DocumentRepositoryDep,
):
    """Get a specific project with details."""

    # Get project
    project = await project_repo.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get document count
    documents = await document_repo.get_by_project_id(project_id)
    document_count = len(documents)

    return ProjectResponse(
        id=str(project.id),
        name=project.name,
        description=project.description,
        status=project.status,
        created_at=project.created_at,
        updated_at=project.updated_at,
        user_id=str(project.user_id),
        document_count=document_count,
    )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    request: UpdateProjectRequest,
    current_user: CurrentUserDep,
    project_repo: SimpleProjectRepositoryDep,
):
    """Update a project."""

    # Get project
    project = await project_repo.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Update fields
    if request.name is not None:
        project.name = request.name
    if request.description is not None:
        project.description = request.description

    project.updated_at = datetime.utcnow()
    project = await project_repo.update(project)

    return ProjectResponse(
        id=str(project.id),
        name=project.name,
        description=project.description,
        status=project.status,
        created_at=project.created_at,
        updated_at=project.updated_at,
        user_id=str(project.user_id),
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    current_user: CurrentUserDep,
    project_repo: SimpleProjectRepositoryDep,
):
    """Delete a project."""

    # Get project to verify it exists
    project = await project_repo.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    await project_repo.delete(project_id)


@router.get("/{project_id}/stats")
async def get_project_stats(
    project_id: UUID,
    current_user: CurrentUserDep,
    project_repo: ProjectRepositoryDep,
):
    """Get project statistics."""
    
    # TODO: Implement actual statistics calculation
    # This would aggregate data from sources, chapters, scripts, videos
    
    return {
        "project_id": str(project_id),
        "sources": {
            "total": 0,
            "pdf_count": 0,
            "url_count": 0,
            "processing": 0,
            "completed": 0,
            "failed": 0,
        },
        "chapters": {
            "total": 0,
            "avg_length": 0,
            "total_words": 0,
        },
        "scripts": {
            "total": 0,
            "completed": 0,
            "estimated_duration": 0,
        },
        "videos": {
            "total": 0,
            "completed": 0,
            "total_duration": 0,
            "total_size_mb": 0,
        },
        "processing_time": {
            "total_seconds": 0,
            "avg_per_source": 0,
        },
    }


@router.post("/{project_id}/process")
async def process_project(
    project_id: UUID,
    current_user: CurrentUserDep,
    project_repo: ProjectRepositoryDep,
):
    """Start processing all sources in a project."""
    
    # TODO: Implement project-wide processing
    # This would:
    # 1. Process all sources (PDF/URL extraction)
    # 2. Extract chapters from processed content
    # 3. Generate scripts for chapters
    # 4. Optionally generate videos
    
    return {
        "project_id": str(project_id),
        "status": "processing_started",
        "message": "Project processing has been queued",
        "estimated_completion": "2024-01-01T12:00:00Z",
    }
