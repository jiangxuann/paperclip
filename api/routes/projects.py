"""
Project management API endpoints.

Handles CRUD operations for projects and project-level operations.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, status
from pydantic import BaseModel, Field, HttpUrl

from core.domain import FileType, UploadStatus

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


class AddURLRequest(BaseModel):
    """Request model for adding a URL document."""
    url: HttpUrl = Field(..., description="URL to process")


class DocumentResponse(BaseModel):
    """Response model for document data."""
    id: str
    project_id: str
    filename: str
    file_type: FileType
    file_size: Optional[int]
    file_url: str
    upload_status: UploadStatus
    metadata: dict
    created_at: datetime


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


# Document endpoints
@router.post("/{project_id}/documents/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    project_id: UUID,
    file: UploadFile = File(...),
    current_user: CurrentUserDep = None,
    project_repo: SimpleProjectRepositoryDep = None,
    document_repo: DocumentRepositoryDep = None,
):
    """Upload a document file to a project."""

    # Verify project exists
    project = await project_repo.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Determine file type
    filename = file.filename.lower()
    if filename.endswith('.pdf'):
        file_type = FileType.PDF
    elif filename.endswith('.txt'):
        file_type = FileType.TXT
    elif filename.endswith('.docx'):
        file_type = FileType.DOCX
    elif filename.endswith('.md'):
        file_type = FileType.MD
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # Read file content to get size
    content = await file.read()
    file_size = len(content)

    # For now, store as base64 or just placeholder URL
    # In production, upload to S3/cloud storage
    import base64
    file_url = f"data:{file.content_type};base64,{base64.b64encode(content).decode()}"

    from uuid import uuid4
    from core.domain import Document

    # Create document entity
    document = Document(
        id=uuid4(),
        project_id=project_id,
        filename=file.filename,
        file_type=file_type,
        file_size=file_size,
        file_url=file_url,
    )

    # Save to database
    document = await document_repo.create(document)

    return DocumentResponse(
        id=str(document.id),
        project_id=str(document.project_id),
        filename=document.filename,
        file_type=document.file_type,
        file_size=document.file_size,
        file_url=document.file_url,
        upload_status=document.upload_status,
        metadata=document.metadata,
        created_at=document.created_at,
    )


@router.post("/{project_id}/documents/url", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def add_url_document(
    project_id: UUID,
    request: AddURLRequest,
    current_user: CurrentUserDep,
    project_repo: SimpleProjectRepositoryDep,
    document_repo: DocumentRepositoryDep,
):
    """Add a URL document to a project."""

    # Verify project exists
    project = await project_repo.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    from uuid import uuid4
    from core.domain import Document

    # Create document entity
    document = Document(
        id=uuid4(),
        project_id=project_id,
        filename=str(request.url),
        file_type=FileType.PDF,  # Will be converted to PDF
        file_url=str(request.url),
    )

    # Save to database
    document = await document_repo.create(document)

    return DocumentResponse(
        id=str(document.id),
        project_id=str(document.project_id),
        filename=document.filename,
        file_type=document.file_type,
        file_size=document.file_size,
        file_url=document.file_url,
        upload_status=document.upload_status,
        metadata=document.metadata,
        created_at=document.created_at,
    )


@router.post("/{project_id}/documents/text", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def add_text_document(
    project_id: UUID,
    text: str = Form(...),
    filename: str = Form(...),
    current_user: CurrentUserDep = None,
    project_repo: SimpleProjectRepositoryDep = None,
    document_repo: DocumentRepositoryDep = None,
):
    """Add a text document to a project."""

    # Verify project exists
    project = await project_repo.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Encode text as data URL
    import base64
    encoded_text = base64.b64encode(text.encode()).decode()
    file_url = f"data:text/plain;base64,{encoded_text}"

    from uuid import uuid4
    from core.domain import Document

    # Create document entity
    document = Document(
        id=uuid4(),
        project_id=project_id,
        filename=filename,
        file_type=FileType.TXT,
        file_size=len(text),
        file_url=file_url,
    )

    # Save to database
    document = await document_repo.create(document)

    return DocumentResponse(
        id=str(document.id),
        project_id=str(document.project_id),
        filename=document.filename,
        file_type=document.file_type,
        file_size=document.file_size,
        file_url=document.file_url,
        upload_status=document.upload_status,
        metadata=document.metadata,
        created_at=document.created_at,
    )


@router.get("/{project_id}/documents", response_model=List[DocumentResponse])
async def list_project_documents(
    project_id: UUID,
    current_user: CurrentUserDep,
    project_repo: SimpleProjectRepositoryDep,
    document_repo: DocumentRepositoryDep,
):
    """List all documents for a project."""

    # Verify project exists
    project = await project_repo.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    documents = await document_repo.get_by_project_id(project_id)

    return [DocumentResponse(
        id=str(d.id),
        project_id=str(d.project_id),
        filename=d.filename,
        file_type=d.file_type,
        file_size=d.file_size,
        file_url=d.file_url,
        upload_status=d.upload_status,
        metadata=d.metadata,
        created_at=d.created_at,
    ) for d in documents]
