"""
Runway ML video generation provider.

Integrates with Runway's Gen-3 Alpha video generation API
for high-quality AI video creation.
"""

import asyncio
import aiohttp
from typing import Dict, Any, Optional
import logging
from datetime import datetime, timedelta

from core.domain import Script, VideoConfig, VideoProvider
from core.exceptions import ProcessingError
from .base import BaseVideoProvider, VideoGenerationJob, VideoGenerationStatus

logger = logging.getLogger(__name__)


class RunwayProvider(BaseVideoProvider):
    """
    Runway ML video generation provider.
    
    Supports Gen-3 Alpha model for text-to-video and image-to-video generation.
    """
    
    BASE_URL = "https://api.runwayml.com/v1"
    
    def _get_provider_name(self) -> VideoProvider:
        """Return the provider enum value."""
        return VideoProvider.RUNWAY
    
    async def generate_video(self, script: Script, config: VideoConfig) -> VideoGenerationJob:
        """Generate video using Runway Gen-3 Alpha."""
        
        try:
            # Parse script into scenes
            scenes = self._parse_script_scenes(script.content)
            
            if not scenes:
                raise ProcessingError("No valid scenes found in script")
            
            # For now, we'll generate one video per script
            # In the future, we could generate separate videos per scene and combine them
            primary_scene = scenes[0]  # Use first scene for main generation
            
            # Build generation request
            request_data = {
                "model": "gen3a_turbo",
                "text_prompt": self._build_text_prompt(primary_scene, config),
                "duration": min(10, max(4, int(primary_scene.get("duration_estimate", 5)))),  # 4-10 seconds
                "aspect_ratio": self._map_aspect_ratio(config.aspect_ratio),
                "seed": None,  # Random seed
            }
            
            # Add image prompt if available (for future enhancement)
            # request_data["image_prompt"] = image_url
            
            # Make API request
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }
                
                async with session.post(
                    f"{self.BASE_URL}/generations",
                    json=request_data,
                    headers=headers
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        raise ProcessingError(f"Runway API error {response.status}: {error_text}")
                    
                    result = await response.json()
                    
                    # Create job object
                    job = VideoGenerationJob(
                        job_id=result["id"],
                        provider=VideoProvider.RUNWAY,
                        status=VideoGenerationStatus.QUEUED,
                        metadata={
                            "model": request_data["model"],
                            "duration": request_data["duration"],
                            "aspect_ratio": request_data["aspect_ratio"],
                            "prompt": request_data["text_prompt"],
                            "script_id": str(script.id),
                        }
                    )
                    
                    logger.info(f"Started Runway video generation: {job.job_id}")
                    return job
                    
        except Exception as e:
            raise ProcessingError(f"Failed to start Runway video generation: {str(e)}") from e
    
    async def check_job_status(self, job_id: str) -> VideoGenerationJob:
        """Check Runway generation job status."""
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                }
                
                async with session.get(
                    f"{self.BASE_URL}/generations/{job_id}",
                    headers=headers
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        raise ProcessingError(f"Runway API error {response.status}: {error_text}")
                    
                    result = await response.json()
                    
                    # Map Runway status to our status
                    runway_status = result.get("status", "unknown")
                    status_mapping = {
                        "PENDING": VideoGenerationStatus.QUEUED,
                        "RUNNING": VideoGenerationStatus.PROCESSING,
                        "SUCCEEDED": VideoGenerationStatus.COMPLETED,
                        "FAILED": VideoGenerationStatus.FAILED,
                        "CANCELLED": VideoGenerationStatus.CANCELLED,
                    }
                    
                    status = status_mapping.get(runway_status, VideoGenerationStatus.PROCESSING)
                    
                    # Calculate progress
                    progress = 0.0
                    if status == VideoGenerationStatus.QUEUED:
                        progress = 10.0
                    elif status == VideoGenerationStatus.PROCESSING:
                        progress = 50.0
                    elif status == VideoGenerationStatus.COMPLETED:
                        progress = 100.0
                    
                    # Estimate completion time
                    estimated_completion = None
                    if status == VideoGenerationStatus.PROCESSING:
                        # Runway typically takes 1-3 minutes
                        estimated_completion = (datetime.utcnow() + timedelta(minutes=2)).isoformat()
                    
                    job = VideoGenerationJob(
                        job_id=job_id,
                        provider=VideoProvider.RUNWAY,
                        status=status,
                        progress=progress,
                        estimated_completion=estimated_completion,
                        error_message=result.get("failure_reason"),
                        result_url=result.get("artifacts", [{}])[0].get("url") if result.get("artifacts") else None,
                        metadata={
                            "runway_status": runway_status,
                            "created_at": result.get("createdAt"),
                            "updated_at": result.get("updatedAt"),
                        }
                    )
                    
                    return job
                    
        except Exception as e:
            raise ProcessingError(f"Failed to check Runway job status: {str(e)}") from e
    
    async def download_video(self, job_id: str, output_path: str) -> Dict[str, Any]:
        """Download completed video from Runway."""
        
        # First check if job is completed
        job = await self.check_job_status(job_id)
        
        if job.status != VideoGenerationStatus.COMPLETED:
            raise ProcessingError(f"Job {job_id} is not completed (status: {job.status})")
        
        if not job.result_url:
            raise ProcessingError(f"No result URL available for job {job_id}")
        
        try:
            # Download video file
            async with aiohttp.ClientSession() as session:
                async with session.get(job.result_url) as response:
                    
                    if response.status != 200:
                        raise ProcessingError(f"Failed to download video: HTTP {response.status}")
                    
                    # Save to output path
                    with open(output_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
                    
                    # Get file metadata
                    import os
                    file_size = os.path.getsize(output_path)
                    
                    # Extract video metadata (would need video processing library for full metadata)
                    metadata = {
                        "file_path": output_path,
                        "file_size": file_size,
                        "format": "mp4",  # Runway typically outputs MP4
                        "provider": "runway",
                        "job_id": job_id,
                        "downloaded_at": datetime.utcnow().isoformat(),
                    }
                    
                    # Try to get video duration and resolution (requires ffprobe or similar)
                    try:
                        video_info = await self._get_video_info(output_path)
                        metadata.update(video_info)
                    except Exception as e:
                        logger.warning(f"Failed to extract video metadata: {str(e)}")
                    
                    logger.info(f"Downloaded Runway video: {output_path}")
                    return metadata
                    
        except Exception as e:
            raise ProcessingError(f"Failed to download Runway video: {str(e)}") from e
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel Runway generation job."""
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                }
                
                async with session.delete(
                    f"{self.BASE_URL}/generations/{job_id}",
                    headers=headers
                ) as response:
                    
                    # Runway may return 404 if job is already completed/cancelled
                    if response.status in [200, 204, 404]:
                        logger.info(f"Cancelled Runway job: {job_id}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to cancel Runway job: {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error cancelling Runway job: {str(e)}")
            return False
    
    def _build_text_prompt(self, scene: Dict[str, Any], config: VideoConfig) -> str:
        """Build text prompt for Runway generation."""
        
        prompt_parts = []
        
        # Add scene title/context
        if scene.get("title"):
            prompt_parts.append(f"Scene: {scene['title']}")
        
        # Add visual description
        if scene.get("visual_description"):
            visual_desc = scene["visual_description"].replace("[", "").replace("]", "")
            prompt_parts.append(visual_desc)
        
        # Add narration context (but not the full narration text)
        if scene.get("narration"):
            narration = scene["narration"][:200]  # Truncate for prompt
            prompt_parts.append(f"Context: {narration}")
        
        # Add style preferences
        style = config.style
        if style:
            prompt_parts.append(f"Style: {style}")
        
        # Add quality descriptors
        prompt_parts.extend([
            "High quality",
            "Professional cinematography",
            "Smooth camera movement",
        ])
        
        return ". ".join(prompt_parts)
    
    def _map_aspect_ratio(self, aspect_ratio: str) -> str:
        """Map our aspect ratio format to Runway's format."""
        mapping = {
            "16:9": "1280:768",
            "9:16": "768:1280", 
            "1:1": "1024:1024",
        }
        return mapping.get(aspect_ratio, "1280:768")
    
    async def _get_video_info(self, video_path: str) -> Dict[str, Any]:
        """Extract video metadata using ffprobe (if available)."""
        try:
            import subprocess
            import json
            
            # Use ffprobe to get video info
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {}
            
            info = json.loads(result.stdout)
            
            # Extract relevant metadata
            video_stream = next(
                (s for s in info.get('streams', []) if s.get('codec_type') == 'video'),
                {}
            )
            
            format_info = info.get('format', {})
            
            return {
                "duration": float(format_info.get('duration', 0)),
                "resolution": f"{video_stream.get('width', 0)}x{video_stream.get('height', 0)}",
                "fps": eval(video_stream.get('r_frame_rate', '0/1')) if video_stream.get('r_frame_rate') else 0,
                "codec": video_stream.get('codec_name', 'unknown'),
            }
            
        except Exception:
            # ffprobe not available or other error
            return {}
    
    async def get_supported_formats(self) -> Dict[str, Any]:
        """Get Runway-specific supported formats."""
        return {
            "formats": ["mp4"],
            "resolutions": ["1280x768", "768x1280", "1024x1024"],
            "aspect_ratios": ["16:9", "9:16", "1:1"],
            "max_duration": 10,  # seconds
            "min_duration": 4,   # seconds
            "models": ["gen3a_turbo"],
        }
    
    async def estimate_cost(self, script: Script, config: VideoConfig) -> Dict[str, Any]:
        """Estimate Runway generation cost."""
        
        # Runway pricing (as of 2024, subject to change)
        base_cost_per_second = 0.05  # Approximate
        
        scenes = self._parse_script_scenes(script.content)
        total_duration = sum(scene.get("duration_estimate", 5) for scene in scenes)
        
        # Runway limits to 10 seconds per generation
        generations_needed = max(1, len(scenes))  # One generation per scene
        
        estimated_cost = generations_needed * base_cost_per_second * min(10, total_duration / generations_needed)
        
        return {
            "estimated_cost": round(estimated_cost, 2),
            "currency": "USD",
            "factors": ["duration", "number_of_scenes"],
            "generations_needed": generations_needed,
            "note": "Pricing is approximate and subject to change",
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Runway API health."""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                }
                
                # Try to list recent generations (lightweight endpoint)
                async with session.get(
                    f"{self.BASE_URL}/generations?limit=1",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    if response.status == 200:
                        return {
                            "provider": "runway",
                            "status": "healthy",
                            "message": "API is accessible",
                            "last_checked": datetime.utcnow().isoformat(),
                        }
                    else:
                        return {
                            "provider": "runway",
                            "status": "unhealthy",
                            "message": f"API returned status {response.status}",
                            "last_checked": datetime.utcnow().isoformat(),
                        }
                        
        except Exception as e:
            return {
                "provider": "runway",
                "status": "unhealthy", 
                "message": f"Health check failed: {str(e)}",
                "last_checked": datetime.utcnow().isoformat(),
            }
