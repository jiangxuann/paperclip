"""
Template-based video generation provider.

Creates videos using pre-designed templates and programmatic composition
instead of AI generation. Good for consistent styling and faster generation.
"""

import asyncio
import os
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
from pathlib import Path

from core.domain import Script, VideoConfig, VideoProvider
from core.exceptions import ProcessingError
from .base import BaseVideoProvider, VideoGenerationJob, VideoGenerationStatus

logger = logging.getLogger(__name__)


class TemplateProvider(BaseVideoProvider):
    """
    Template-based video generation provider.
    
    Uses programmatic video composition with templates instead of AI generation.
    Faster and more predictable than AI providers, good for educational content.
    """
    
    def __init__(self, api_key: str = "", config: Dict[str, Any] = None):
        """Initialize template provider."""
        super().__init__(api_key, config)
        self.templates_dir = Path(config.get("templates_dir", "templates")) if config else Path("templates")
        self.output_dir = Path(config.get("output_dir", "output")) if config else Path("output")
        
        # Ensure directories exist
        self.templates_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
    
    def _get_provider_name(self) -> VideoProvider:
        """Return the provider enum value."""
        return VideoProvider.TEMPLATE
    
    async def generate_video(self, script: Script, config: VideoConfig) -> VideoGenerationJob:
        """Generate video using template composition."""
        
        try:
            # Parse script into scenes
            scenes = self._parse_script_scenes(script.content)
            
            if not scenes:
                raise ProcessingError("No valid scenes found in script")
            
            # Create job ID
            job_id = f"template_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(script.content) % 10000}"
            
            # Start async video generation
            asyncio.create_task(self._generate_video_async(job_id, script, scenes, config))
            
            job = VideoGenerationJob(
                job_id=job_id,
                provider=VideoProvider.TEMPLATE,
                status=VideoGenerationStatus.QUEUED,
                metadata={
                    "scene_count": len(scenes),
                    "template_style": config.style,
                    "script_id": str(script.id),
                    "estimated_duration": sum(scene.get("duration_estimate", 5) for scene in scenes),
                }
            )
            
            logger.info(f"Started template video generation: {job.job_id}")
            return job
            
        except Exception as e:
            raise ProcessingError(f"Failed to start template video generation: {str(e)}") from e
    
    async def _generate_video_async(self, job_id: str, script: Script, scenes: List[Dict[str, Any]], config: VideoConfig):
        """Async video generation task."""
        
        try:
            # Update job status file
            await self._update_job_status(job_id, VideoGenerationStatus.PROCESSING, 10.0)
            
            # Generate video scenes
            scene_files = []
            
            for i, scene in enumerate(scenes):
                logger.info(f"Generating scene {i + 1}/{len(scenes)} for job {job_id}")
                
                scene_file = await self._generate_scene_video(scene, config, i + 1)
                scene_files.append(scene_file)
                
                # Update progress
                progress = 10.0 + (i + 1) / len(scenes) * 70.0  # 10% to 80%
                await self._update_job_status(job_id, VideoGenerationStatus.PROCESSING, progress)
            
            # Combine scenes into final video
            logger.info(f"Combining scenes for job {job_id}")
            final_video = await self._combine_scenes(scene_files, job_id)
            
            # Update job status
            await self._update_job_status(job_id, VideoGenerationStatus.COMPLETED, 100.0, final_video)
            
            # Cleanup intermediate files
            for scene_file in scene_files:
                try:
                    os.remove(scene_file)
                except Exception as e:
                    logger.warning(f"Failed to cleanup scene file {scene_file}: {e}")
            
            logger.info(f"Completed template video generation: {job_id}")
            
        except Exception as e:
            logger.error(f"Template video generation failed for {job_id}: {str(e)}")
            await self._update_job_status(job_id, VideoGenerationStatus.FAILED, 0.0, error=str(e))
    
    async def _generate_scene_video(self, scene: Dict[str, Any], config: VideoConfig, scene_number: int) -> str:
        """Generate video for a single scene using templates."""
        
        # This would use a video composition library like moviepy, ffmpeg-python, etc.
        # For now, we'll create a placeholder implementation
        
        scene_title = scene.get("title", f"Scene {scene_number}")
        narration = scene.get("narration", "")
        duration = scene.get("duration_estimate", 5.0)
        
        # Create scene video (placeholder implementation)
        scene_file = self.output_dir / f"scene_{scene_number}_{datetime.utcnow().strftime('%H%M%S')}.mp4"
        
        # In a real implementation, you would:
        # 1. Load template video/image assets
        # 2. Add text overlays with scene title and key points
        # 3. Generate or add background visuals
        # 4. Add narration audio (TTS)
        # 5. Compose everything into a video file
        
        # For placeholder, create a simple text file representing the video
        placeholder_content = f"""Template Video Scene {scene_number}
Title: {scene_title}
Duration: {duration}s
Narration: {narration[:200]}...
Generated: {datetime.utcnow().isoformat()}

This would be actual video content in a real implementation.
Template style: {config.style}
Quality: {config.quality}
"""
        
        with open(scene_file, 'w') as f:
            f.write(placeholder_content)
        
        # Simulate processing time
        await asyncio.sleep(2)  # 2 seconds per scene
        
        return str(scene_file)
    
    async def _combine_scenes(self, scene_files: List[str], job_id: str) -> str:
        """Combine individual scene videos into final video."""
        
        final_video_path = self.output_dir / f"video_{job_id}.mp4"
        
        # In a real implementation, you would:
        # 1. Use ffmpeg or moviepy to concatenate scene videos
        # 2. Add transitions between scenes
        # 3. Add intro/outro if configured
        # 4. Apply consistent audio levels
        # 5. Export in desired format and quality
        
        # For placeholder, combine text files
        combined_content = f"Combined Template Video - Job {job_id}\n"
        combined_content += f"Generated: {datetime.utcnow().isoformat()}\n\n"
        
        for i, scene_file in enumerate(scene_files):
            combined_content += f"=== SCENE {i + 1} ===\n"
            try:
                with open(scene_file, 'r') as f:
                    combined_content += f.read()
                combined_content += "\n\n"
            except Exception as e:
                combined_content += f"Error reading scene file: {e}\n\n"
        
        with open(final_video_path, 'w') as f:
            f.write(combined_content)
        
        # Simulate final processing time
        await asyncio.sleep(3)
        
        return str(final_video_path)
    
    async def _update_job_status(self, job_id: str, status: VideoGenerationStatus, 
                               progress: float, result_url: str = None, error: str = None):
        """Update job status in a status file."""
        
        status_file = self.output_dir / f"status_{job_id}.json"
        
        status_data = {
            "job_id": job_id,
            "status": status.value,
            "progress": progress,
            "updated_at": datetime.utcnow().isoformat(),
        }
        
        if result_url:
            status_data["result_url"] = result_url
        
        if error:
            status_data["error"] = error
        
        import json
        with open(status_file, 'w') as f:
            json.dump(status_data, f, indent=2)
    
    async def check_job_status(self, job_id: str) -> VideoGenerationJob:
        """Check template generation job status."""
        
        try:
            status_file = self.output_dir / f"status_{job_id}.json"
            
            if not status_file.exists():
                # Job not found, might be very new
                return VideoGenerationJob(
                    job_id=job_id,
                    provider=VideoProvider.TEMPLATE,
                    status=VideoGenerationStatus.QUEUED,
                    progress=0.0,
                )
            
            import json
            with open(status_file, 'r') as f:
                status_data = json.load(f)
            
            status = VideoGenerationStatus(status_data.get("status", "processing"))
            
            job = VideoGenerationJob(
                job_id=job_id,
                provider=VideoProvider.TEMPLATE,
                status=status,
                progress=status_data.get("progress", 0.0),
                result_url=status_data.get("result_url"),
                error_message=status_data.get("error"),
                metadata={
                    "updated_at": status_data.get("updated_at"),
                    "template_based": True,
                }
            )
            
            return job
            
        except Exception as e:
            raise ProcessingError(f"Failed to check template job status: {str(e)}") from e
    
    async def download_video(self, job_id: str, output_path: str) -> Dict[str, Any]:
        """Download completed template video."""
        
        job = await self.check_job_status(job_id)
        
        if job.status != VideoGenerationStatus.COMPLETED:
            raise ProcessingError(f"Job {job_id} is not completed (status: {job.status})")
        
        if not job.result_url:
            raise ProcessingError(f"No result URL available for job {job_id}")
        
        try:
            # Copy file from result location to output path
            import shutil
            shutil.copy2(job.result_url, output_path)
            
            file_size = os.path.getsize(output_path)
            
            metadata = {
                "file_path": output_path,
                "file_size": file_size,
                "format": "mp4",  # Would be actual format
                "provider": "template",
                "job_id": job_id,
                "downloaded_at": datetime.utcnow().isoformat(),
                "template_based": True,
            }
            
            logger.info(f"Downloaded template video: {output_path}")
            return metadata
            
        except Exception as e:
            raise ProcessingError(f"Failed to download template video: {str(e)}") from e
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel template generation job."""
        
        try:
            # Update status to cancelled
            await self._update_job_status(job_id, VideoGenerationStatus.CANCELLED, 0.0)
            
            logger.info(f"Cancelled template job: {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling template job: {str(e)}")
            return False
    
    async def get_supported_formats(self) -> Dict[str, Any]:
        """Get template-specific supported formats."""
        return {
            "formats": ["mp4", "mov", "avi"],
            "resolutions": ["1920x1080", "1280x720", "854x480"],
            "aspect_ratios": ["16:9", "9:16", "1:1", "4:3"],
            "max_duration": 600,  # 10 minutes
            "min_duration": 5,    # 5 seconds
            "templates": ["educational", "documentary", "presentation", "tutorial"],
            "customizable": True,
        }
    
    async def estimate_cost(self, script: Script, config: VideoConfig) -> Dict[str, Any]:
        """Estimate template generation cost."""
        
        # Template generation is typically much cheaper
        scenes = self._parse_script_scenes(script.content)
        total_duration = sum(scene.get("duration_estimate", 5) for scene in scenes)
        
        # Cost based on processing time and resources
        estimated_cost = max(0.01, total_duration * 0.001)  # Very low cost
        
        return {
            "estimated_cost": round(estimated_cost, 3),
            "currency": "USD",
            "factors": ["duration", "template_complexity"],
            "note": "Template generation is typically very cost-effective",
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check template generation system health."""
        
        try:
            # Check if directories are accessible
            templates_accessible = self.templates_dir.exists() and os.access(self.templates_dir, os.W_OK)
            output_accessible = self.output_dir.exists() and os.access(self.output_dir, os.W_OK)
            
            if templates_accessible and output_accessible:
                status = "healthy"
                message = "Template generation system is operational"
            else:
                status = "unhealthy"
                message = "Directory access issues detected"
            
            return {
                "provider": "template",
                "status": status,
                "message": message,
                "templates_dir": str(self.templates_dir),
                "output_dir": str(self.output_dir),
                "templates_accessible": templates_accessible,
                "output_accessible": output_accessible,
                "last_checked": datetime.utcnow().isoformat(),
            }
            
        except Exception as e:
            return {
                "provider": "template",
                "status": "unhealthy",
                "message": f"Health check failed: {str(e)}",
                "last_checked": datetime.utcnow().isoformat(),
            }
