"""
A/B testing API endpoints.

Handles A/B test creation, management, and result analysis.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Body
from pydantic import BaseModel, Field

from core.domain.entities import TestMetric, ABTestStatus, ProjectId, VideoId
from ..dependencies import (
    CurrentUserDep,
    ABTestRepositoryDep,  # Will need to add this
)

router = APIRouter()


# Request/Response models
class CreateABTestRequest(BaseModel):
    """Request model for creating an A/B test."""
    project_id: UUID = Field(..., description="Project ID")
    test_name: str = Field(..., description="Name of the test")
    variant_a_video_id: Optional[UUID] = Field(None, description="Video ID for variant A")
    variant_b_video_id: Optional[UUID] = Field(None, description="Video ID for variant B")
    test_metric: TestMetric = Field(..., description="Metric to test")
    sample_size: Optional[int] = Field(None, description="Target sample size")


class ABTestResponse(BaseModel):
    """Response model for A/B test data."""
    id: str
    project_id: str
    test_name: str
    variant_a_video_id: Optional[str] = None
    variant_b_video_id: Optional[str] = None
    test_metric: TestMetric
    sample_size: Optional[int] = None
    confidence_level: Optional[float] = None
    results: Optional[Dict[str, Any]] = None
    status: ABTestStatus
    created_at: datetime


class ABTestResultsResponse(BaseModel):
    """Response model for A/B test results."""
    test_id: str
    status: ABTestStatus
    results: Optional[Dict[str, Any]] = None
    winner: Optional[str] = None
    confidence_level: Optional[float] = None
    sample_size_achieved: Optional[int] = None


@router.post("/", response_model=ABTestResponse, status_code=status.HTTP_201_CREATED)
async def create_ab_test(
    request: CreateABTestRequest,
    current_user: CurrentUserDep,
    ab_test_repo: ABTestRepositoryDep,
):
    """Create a new A/B test."""
    test = ABTest(
        id=UUID(),
        project_id=ProjectId(request.project_id),
        test_name=request.test_name,
        variant_a_video_id=VideoId(request.variant_a_video_id) if request.variant_a_video_id else None,
        variant_b_video_id=VideoId(request.variant_b_video_id) if request.variant_b_video_id else None,
        test_metric=request.test_metric,
        sample_size=request.sample_size
    )

    created_test = await ab_test_repo.create(test)

    return ABTestResponse(
        id=str(created_test.id),
        project_id=str(created_test.project_id),
        test_name=created_test.test_name,
        variant_a_video_id=str(created_test.variant_a_video_id) if created_test.variant_a_video_id else None,
        variant_b_video_id=str(created_test.variant_b_video_id) if created_test.variant_b_video_id else None,
        test_metric=created_test.test_metric,
        sample_size=created_test.sample_size,
        confidence_level=created_test.confidence_level,
        results=created_test.results,
        status=created_test.status,
        created_at=created_test.created_at
    )


@router.get("/{test_id}", response_model=ABTestResponse)
async def get_ab_test(
    test_id: UUID,
    current_user: CurrentUserDep,
    ab_test_repo: ABTestRepositoryDep,
):
    """Get a specific A/B test."""
    test = await ab_test_repo.get_by_id(test_id)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"A/B test {test_id} not found"
        )

    return ABTestResponse(
        id=str(test.id),
        project_id=str(test.project_id),
        test_name=test.test_name,
        variant_a_video_id=str(test.variant_a_video_id) if test.variant_a_video_id else None,
        variant_b_video_id=str(test.variant_b_video_id) if test.variant_b_video_id else None,
        test_metric=test.test_metric,
        sample_size=test.sample_size,
        confidence_level=test.confidence_level,
        results=test.results,
        status=test.status,
        created_at=test.created_at
    )


@router.put("/{test_id}", response_model=ABTestResponse)
async def update_ab_test(
    test_id: UUID,
    current_user: CurrentUserDep,
    ab_test_repo: ABTestRepositoryDep,
    test_name: Optional[str] = Body(None, description="Test name"),
    variant_a_video_id: Optional[UUID] = Body(None, description="Variant A video ID"),
    variant_b_video_id: Optional[UUID] = Body(None, description="Variant B video ID"),
    sample_size: Optional[int] = Body(None, description="Sample size"),
):
    """Update an A/B test."""
    test = await ab_test_repo.get_by_id(test_id)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"A/B test {test_id} not found"
        )

    # Update fields
    if test_name is not None:
        test.test_name = test_name
    if variant_a_video_id is not None:
        test.variant_a_video_id = VideoId(variant_a_video_id)
    if variant_b_video_id is not None:
        test.variant_b_video_id = VideoId(variant_b_video_id)
    if sample_size is not None:
        test.sample_size = sample_size

    updated_test = await ab_test_repo.update(test)

    return ABTestResponse(
        id=str(updated_test.id),
        project_id=str(updated_test.project_id),
        test_name=updated_test.test_name,
        variant_a_video_id=str(updated_test.variant_a_video_id) if updated_test.variant_a_video_id else None,
        variant_b_video_id=str(updated_test.variant_b_video_id) if updated_test.variant_b_video_id else None,
        test_metric=updated_test.test_metric,
        sample_size=updated_test.sample_size,
        confidence_level=updated_test.confidence_level,
        results=updated_test.results,
        status=updated_test.status,
        created_at=updated_test.created_at
    )


@router.post("/{test_id}/complete")
async def complete_ab_test(
    test_id: UUID,
    results: Dict[str, Any] = Body(..., description="Test results"),
    current_user: CurrentUserDep,
    ab_test_repo: ABTestRepositoryDep,
):
    """Mark an A/B test as completed with results."""
    test = await ab_test_repo.get_by_id(test_id)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"A/B test {test_id} not found"
        )

    test.mark_completed(results)
    updated_test = await ab_test_repo.update(test)

    return {
        "test_id": str(test_id),
        "status": "completed",
        "results": results,
        "message": f"A/B test {test_id} marked as completed"
    }


@router.post("/{test_id}/pause")
async def pause_ab_test(
    test_id: UUID,
    current_user: CurrentUserDep,
    ab_test_repo: ABTestRepositoryDep,
):
    """Pause an A/B test."""
    test = await ab_test_repo.get_by_id(test_id)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"A/B test {test_id} not found"
        )

    if test.status != ABTestStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Test {test_id} is not running"
        )

    test.mark_paused()
    await ab_test_repo.update(test)

    return {
        "test_id": str(test_id),
        "status": "paused",
        "message": f"A/B test {test_id} has been paused"
    }


@router.post("/{test_id}/resume")
async def resume_ab_test(
    test_id: UUID,
    current_user: CurrentUserDep,
    ab_test_repo: ABTestRepositoryDep,
):
    """Resume a paused A/B test."""
    test = await ab_test_repo.get_by_id(test_id)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"A/B test {test_id} not found"
        )

    if test.status != ABTestStatus.PAUSED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Test {test_id} is not paused"
        )

    test.resume()
    await ab_test_repo.update(test)

    return {
        "test_id": str(test_id),
        "status": "running",
        "message": f"A/B test {test_id} has been resumed"
    }


@router.get("/project/{project_id}", response_model=List[ABTestResponse])
async def list_project_ab_tests(
    project_id: UUID,
    current_user: CurrentUserDep,
    ab_test_repo: ABTestRepositoryDep,
):
    """List all A/B tests for a project."""
    tests = await ab_test_repo.get_by_project_id(ProjectId(project_id))

    return [ABTestResponse(
        id=str(test.id),
        project_id=str(test.project_id),
        test_name=test.test_name,
        variant_a_video_id=str(test.variant_a_video_id) if test.variant_a_video_id else None,
        variant_b_video_id=str(test.variant_b_video_id) if test.variant_b_video_id else None,
        test_metric=test.test_metric,
        sample_size=test.sample_size,
        confidence_level=test.confidence_level,
        results=test.results,
        status=test.status,
        created_at=test.created_at
    ) for test in tests]


@router.get("/active", response_model=List[ABTestResponse])
async def list_active_ab_tests(
    current_user: CurrentUserDep,
    ab_test_repo: ABTestRepositoryDep,
):
    """List all active A/B tests."""
    tests = await ab_test_repo.get_active_tests()

    return [ABTestResponse(
        id=str(test.id),
        project_id=str(test.project_id),
        test_name=test.test_name,
        variant_a_video_id=str(test.variant_a_video_id) if test.variant_a_video_id else None,
        variant_b_video_id=str(test.variant_b_video_id) if test.variant_b_video_id else None,
        test_metric=test.test_metric,
        sample_size=test.sample_size,
        confidence_level=test.confidence_level,
        results=test.results,
        status=test.status,
        created_at=test.created_at
    ) for test in tests]


@router.get("/video/{video_id}", response_model=List[ABTestResponse])
async def list_video_ab_tests(
    video_id: UUID,
    current_user: CurrentUserDep,
    ab_test_repo: ABTestRepositoryDep,
):
    """List all A/B tests that include a specific video."""
    tests = await ab_test_repo.get_tests_by_video(VideoId(video_id))

    return [ABTestResponse(
        id=str(test.id),
        project_id=str(test.project_id),
        test_name=test.test_name,
        variant_a_video_id=str(test.variant_a_video_id) if test.variant_a_video_id else None,
        variant_b_video_id=str(test.variant_b_video_id) if test.variant_b_video_id else None,
        test_metric=test.test_metric,
        sample_size=test.sample_size,
        confidence_level=test.confidence_level,
        results=test.results,
        status=test.status,
        created_at=test.created_at
    ) for test in tests]


@router.delete("/{test_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ab_test(
    test_id: UUID,
    current_user: CurrentUserDep,
    ab_test_repo: ABTestRepositoryDep,
):
    """Delete an A/B test."""
    test = await ab_test_repo.get_by_id(test_id)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"A/B test {test_id} not found"
        )

    await ab_test_repo.delete(test_id)