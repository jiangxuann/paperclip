"""
Video analytics API endpoints.

Handles video performance tracking and analytics.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Body
from pydantic import BaseModel, Field

from core.domain.entities import VideoId
from ..dependencies import (
    CurrentUserDep,
    VideoAnalyticsRepositoryDep,  # Will need to add this
)

router = APIRouter()


# Request/Response models
class TrackViewRequest(BaseModel):
    """Request model for tracking a video view."""
    video_id: UUID = Field(..., description="Video ID")
    platform: str = Field(..., description="Platform where view occurred")
    count: int = Field(1, ge=1, description="Number of views to add")


class AnalyticsResponse(BaseModel):
    """Response model for analytics data."""
    id: str
    video_id: str
    platform: str
    views: int
    created_at: datetime


class VideoStatsResponse(BaseModel):
    """Response model for video statistics."""
    video_id: str
    total_views: int
    platform_stats: Dict[str, int]
    analytics_records: List[AnalyticsResponse]


@router.post("/track-view", response_model=AnalyticsResponse)
async def track_video_view(
    request: TrackViewRequest,
    current_user: CurrentUserDep,
    analytics_repo: VideoAnalyticsRepositoryDep,
):
    """Track a view for a video on a specific platform."""
    analytics = await analytics_repo.increment_views(
        VideoId(request.video_id),
        request.platform,
        request.count
    )

    return AnalyticsResponse(
        id=str(analytics.id),
        video_id=str(analytics.video_id),
        platform=analytics.platform,
        views=analytics.views,
        created_at=analytics.created_at
    )


@router.get("/video/{video_id}", response_model=VideoStatsResponse)
async def get_video_analytics(
    video_id: UUID,
    current_user: CurrentUserDep,
    analytics_repo: VideoAnalyticsRepositoryDep,
):
    """Get analytics for a specific video."""
    # Get all analytics records for the video
    records = await analytics_repo.get_by_video_id(VideoId(video_id))

    # Get total views and platform breakdown
    total_views = await analytics_repo.get_total_views(VideoId(video_id))
    platform_stats = await analytics_repo.get_platform_stats(VideoId(video_id))

    return VideoStatsResponse(
        video_id=str(video_id),
        total_views=total_views,
        platform_stats=platform_stats,
        analytics_records=[AnalyticsResponse(
            id=str(record.id),
            video_id=str(record.video_id),
            platform=record.platform,
            views=record.views,
            created_at=record.created_at
        ) for record in records]
    )


@router.get("/video/{video_id}/platform/{platform}", response_model=AnalyticsResponse)
async def get_platform_analytics(
    video_id: UUID,
    platform: str,
    current_user: CurrentUserDep,
    analytics_repo: VideoAnalyticsRepositoryDep,
):
    """Get analytics for a video on a specific platform."""
    analytics = await analytics_repo.get_by_platform(VideoId(video_id), platform)

    if not analytics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No analytics found for video {video_id} on platform {platform}"
        )

    return AnalyticsResponse(
        id=str(analytics.id),
        video_id=str(analytics.video_id),
        platform=analytics.platform,
        views=analytics.views,
        created_at=analytics.created_at
    )


@router.post("/video/{video_id}/increment-views")
async def increment_video_views(
    video_id: UUID,
    current_user: CurrentUserDep,
    analytics_repo: VideoAnalyticsRepositoryDep,
    platform: str = Body(..., description="Platform name"),
    count: int = Body(1, ge=1, description="Number of views to add"),
):
    """Increment view count for a video on a platform."""
    analytics = await analytics_repo.increment_views(VideoId(video_id), platform, count)

    return {
        "video_id": str(video_id),
        "platform": platform,
        "views_added": count,
        "total_views": analytics.views,
        "message": f"Added {count} views to video {video_id} on {platform}"
    }


@router.get("/video/{video_id}/total-views")
async def get_total_views(
    video_id: UUID,
    current_user: CurrentUserDep,
    analytics_repo: VideoAnalyticsRepositoryDep,
):
    """Get total view count for a video across all platforms."""
    total_views = await analytics_repo.get_total_views(VideoId(video_id))

    return {
        "video_id": str(video_id),
        "total_views": total_views
    }


@router.get("/video/{video_id}/platform-stats")
async def get_platform_stats(
    video_id: UUID,
    current_user: CurrentUserDep,
    analytics_repo: VideoAnalyticsRepositoryDep,
):
    """Get view statistics by platform for a video."""
    platform_stats = await analytics_repo.get_platform_stats(VideoId(video_id))

    return {
        "video_id": str(video_id),
        "platform_stats": platform_stats,
        "platforms_count": len(platform_stats)
    }