"""
Main video generation orchestrator.

Manages video generation across multiple providers and handles
job scheduling, monitoring, and result aggregation.
"""

import asyncio
from typing import Dict, Any, Optional, List, Type
import logging
from datetime import datetime
from pathlib import Path

from core.domain import Script, Video, VideoId, VideoProvider, VideoConfig, ProcessingStatus
from core.exceptions import ProcessingError
from ..providers import (
    BaseVideoProvider, 
    RunwayProvider, 
    PikaProvider, 
    LumaProvider, 
    TemplateProvider,
    VideoGenerationJob,
    VideoGenerationStatus
)

logger = logging.getLogger(__name__)


class VideoGenerator:
    """
    Main video generation orchestrator.
    
    Manages multiple video providers and provides a unified interface
    for video generation with automatic provider selection and fallback.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize video generator with configuration."""
        self.config = config or {}
        self.providers: Dict[VideoProvider, BaseVideoProvider] = {}
        self.active_jobs: Dict[str, VideoGenerationJob] = {}
        
        # Initialize available providers
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize video generation providers based on configuration."""
        
        provider_configs = self.config.get("providers", {})
        
        # Runway provider
        runway_config = provider_configs.get("runway", {})
        if runway_config.get("api_key"):
            try:
                self.providers[VideoProvider.RUNWAY] = RunwayProvider(
                    api_key=runway_config["api_key"],
                    config=runway_config
                )
                logger.info("Initialized Runway provider")
            except Exception as e:
                logger.warning(f"Failed to initialize Runway provider: {e}")
        
        # Pika provider
        pika_config = provider_configs.get("pika", {})
        if pika_config.get("api_key"):
            try:
                self.providers[VideoProvider.PIKA] = PikaProvider(
                    api_key=pika_config["api_key"],
                    config=pika_config
                )
                logger.info("Initialized Pika provider")
            except Exception as e:
                logger.warning(f"Failed to initialize Pika provider: {e}")
        
        # Luma provider
        luma_config = provider_configs.get("luma", {})
        if luma_config.get("api_key"):
            try:
                self.providers[VideoProvider.LUMA] = LumaProvider(
                    api_key=luma_config["api_key"],
                    config=luma_config
                )
                logger.info("Initialized Luma provider")
            except Exception as e:
                logger.warning(f"Failed to initialize Luma provider: {e}")
        
        # Template provider (always available)
        template_config = provider_configs.get("template", {})
        try:
            self.providers[VideoProvider.TEMPLATE] = TemplateProvider(
                config=template_config
            )
            logger.info("Initialized Template provider")
        except Exception as e:
            logger.warning(f"Failed to initialize Template provider: {e}")
        
        if not self.providers:
            raise ProcessingError("No video providers available")
        
        logger.info(f"Initialized {len(self.providers)} video providers: {list(self.providers.keys())}")
    
    async def generate_video(self, script: Script, provider: VideoProvider = None, 
                           config: VideoConfig = None) -> Video:
        """
        Generate video from script.
        
        Args:
            script: Script entity to generate video from
            provider: Specific provider to use (optional, will auto-select if None)
            config: Video generation configuration
            
        Returns:
            Video entity with generation job information
        """
        
        if not config:
            config = VideoConfig({})
        
        # Select provider
        selected_provider = await self._select_provider(script, provider, config)
        
        if not selected_provider:
            raise ProcessingError("No suitable video provider available")
        
        # Create video entity
        video = Video(
            id=VideoId.generate(),
            project_id=script.project_id,
            script_id=script.id,
            title=f"Video: {script.title}",
            provider=selected_provider,
            config=config,
        )
        
        try:
            # Start generation
            video.mark_generating("pending")
            
            provider_instance = self.providers[selected_provider]
            
            # Validate script
            validation = await provider_instance.validate_script(script)
            if not validation["valid"]:
                raise ProcessingError(f"Script validation failed: {validation['issues']}")
            
            if validation["warnings"]:
                logger.warning(f"Script validation warnings: {validation['warnings']}")
            
            # Start generation job
            job = await provider_instance.generate_video(script, config)
            
            # Update video with job information
            video.mark_generating(job.job_id)
            
            # Track job
            self.active_jobs[job.job_id] = job
            
            logger.info(f"Started video generation: {video.id} using {selected_provider.value}")
            return video
            
        except Exception as e:
            error_msg = f"Failed to generate video: {str(e)}"
            logger.error(error_msg)
            video.mark_failed(error_msg)
            raise ProcessingError(error_msg) from e
    
    async def _select_provider(self, script: Script, preferred_provider: VideoProvider = None, 
                             config: VideoConfig = None) -> Optional[VideoProvider]:
        """Select the best provider for video generation."""
        
        # If specific provider requested, use it if available
        if preferred_provider and preferred_provider in self.providers:
            # Check if provider is healthy
            provider_instance = self.providers[preferred_provider]
            health = await provider_instance.health_check()
            
            if health["status"] == "healthy":
                return preferred_provider
            else:
                logger.warning(f"Preferred provider {preferred_provider.value} is unhealthy: {health['message']}")
        
        # Auto-select based on script characteristics and provider capabilities
        return await self._auto_select_provider(script, config)
    
    async def _auto_select_provider(self, script: Script, config: VideoConfig) -> Optional[VideoProvider]:
        """Automatically select the best provider based on requirements."""
        
        # Provider selection criteria
        selection_criteria = {
            "duration": script.estimated_duration or 5.0,
            "quality": config.quality,
            "style": config.style,
            "budget": config.get("max_cost", float('inf')),
        }
        
        # Score providers
        provider_scores = {}
        
        for provider_type, provider_instance in self.providers.items():
            try:
                # Check health
                health = await provider_instance.health_check()
                if health["status"] != "healthy" and health["status"] != "placeholder":
                    continue
                
                # Get capabilities
                capabilities = await provider_instance.get_supported_formats()
                
                # Calculate score
                score = await self._score_provider(provider_type, capabilities, selection_criteria, script, config)
                
                if score > 0:
                    provider_scores[provider_type] = score
                    
            except Exception as e:
                logger.warning(f"Error evaluating provider {provider_type.value}: {e}")
                continue
        
        if not provider_scores:
            return None
        
        # Select highest scoring provider
        best_provider = max(provider_scores.keys(), key=lambda p: provider_scores[p])
        
        logger.info(f"Auto-selected provider: {best_provider.value} (score: {provider_scores[best_provider]:.2f})")
        return best_provider
    
    async def _score_provider(self, provider_type: VideoProvider, capabilities: Dict[str, Any], 
                            criteria: Dict[str, Any], script: Script, config: VideoConfig) -> float:
        """Score a provider based on selection criteria."""
        
        score = 0.0
        
        # Duration compatibility
        max_duration = capabilities.get("max_duration", 60)
        if criteria["duration"] <= max_duration:
            score += 30.0
        else:
            score -= 20.0  # Penalty for duration mismatch
        
        # Quality preference
        if criteria["quality"] == "4k" and "4k" in str(capabilities.get("resolutions", [])):
            score += 20.0
        elif criteria["quality"] == "1080p":
            score += 15.0
        
        # Style compatibility
        if provider_type == VideoProvider.TEMPLATE and criteria["style"] in ["educational", "presentation"]:
            score += 25.0
        elif provider_type in [VideoProvider.RUNWAY, VideoProvider.LUMA] and criteria["style"] == "documentary":
            score += 20.0
        
        # Cost consideration
        try:
            provider_instance = self.providers[provider_type]
            cost_estimate = await provider_instance.estimate_cost(script, config)
            estimated_cost = cost_estimate.get("estimated_cost", 0)
            
            if estimated_cost <= criteria["budget"]:
                # Lower cost = higher score (up to 15 points)
                score += max(0, 15 - estimated_cost * 10)
            else:
                score -= 30.0  # Heavy penalty for exceeding budget
                
        except Exception:
            # If cost estimation fails, assume moderate cost
            score += 5.0
        
        # Provider-specific bonuses
        if provider_type == VideoProvider.TEMPLATE:
            score += 10.0  # Bonus for reliability and speed
        elif provider_type == VideoProvider.RUNWAY:
            score += 15.0  # Bonus for quality and reliability
        
        return max(0.0, score)
    
    async def check_video_status(self, video: Video) -> Video:
        """Check and update video generation status."""
        
        if not video.provider_job_id:
            return video
        
        try:
            provider_instance = self.providers[video.provider]
            job = await provider_instance.check_job_status(video.provider_job_id)
            
            # Update active jobs tracking
            self.active_jobs[job.job_id] = job
            
            # Update video based on job status
            if job.status == VideoGenerationStatus.COMPLETED and job.result_url:
                # Download video if not already downloaded
                if not video.file_path:
                    output_path = self._get_output_path(video)
                    metadata = await provider_instance.download_video(job.job_id, output_path)
                    video.mark_completed(output_path, metadata)
                
            elif job.status == VideoGenerationStatus.FAILED:
                video.mark_failed(job.error_message or "Video generation failed")
                
            elif job.status == VideoGenerationStatus.PROCESSING:
                # Video is still processing, no update needed
                pass
            
            return video
            
        except Exception as e:
            error_msg = f"Failed to check video status: {str(e)}"
            logger.error(error_msg)
            video.mark_failed(error_msg)
            return video
    
    def _get_output_path(self, video: Video) -> str:
        """Generate output path for video file."""
        
        output_dir = Path(self.config.get("output_dir", "output/videos"))
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"video_{video.id}_{video.provider.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.mp4"
        return str(output_dir / filename)
    
    async def cancel_video_generation(self, video: Video) -> bool:
        """Cancel video generation."""
        
        if not video.provider_job_id:
            return False
        
        try:
            provider_instance = self.providers[video.provider]
            success = await provider_instance.cancel_job(video.provider_job_id)
            
            if success:
                video.mark_failed("Generation cancelled by user")
                
                # Remove from active jobs
                if video.provider_job_id in self.active_jobs:
                    del self.active_jobs[video.provider_job_id]
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to cancel video generation: {str(e)}")
            return False
    
    async def generate_batch_videos(self, scripts: List[Script], 
                                  provider: VideoProvider = None,
                                  config: VideoConfig = None) -> List[Video]:
        """Generate videos for multiple scripts in batch."""
        
        videos = []
        
        # Limit concurrent generations to avoid overwhelming providers
        semaphore = asyncio.Semaphore(3)
        
        async def generate_single_video(script: Script) -> Video:
            async with semaphore:
                return await self.generate_video(script, provider, config)
        
        # Create tasks
        tasks = [generate_single_video(script) for script in scripts]
        
        # Execute with progress logging
        for i, task in enumerate(asyncio.as_completed(tasks)):
            try:
                video = await task
                videos.append(video)
                logger.info(f"Started video generation {i + 1}/{len(scripts)}")
            except Exception as e:
                logger.error(f"Failed to start video generation {i + 1}: {str(e)}")
                continue
        
        return videos
    
    async def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all available providers."""
        
        provider_status = {}
        
        for provider_type, provider_instance in self.providers.items():
            try:
                health = await provider_instance.health_check()
                capabilities = await provider_instance.get_supported_formats()
                
                provider_status[provider_type.value] = {
                    "health": health,
                    "capabilities": capabilities,
                }
                
            except Exception as e:
                provider_status[provider_type.value] = {
                    "health": {
                        "status": "error",
                        "message": f"Status check failed: {str(e)}",
                    },
                    "capabilities": {},
                }
        
        return provider_status
    
    async def estimate_generation_cost(self, scripts: List[Script], 
                                     provider: VideoProvider = None,
                                     config: VideoConfig = None) -> Dict[str, Any]:
        """Estimate total cost for generating videos from scripts."""
        
        if not config:
            config = VideoConfig({})
        
        total_estimates = {}
        
        # Get estimates from each provider (or just the specified one)
        providers_to_check = [provider] if provider else list(self.providers.keys())
        
        for provider_type in providers_to_check:
            if provider_type not in self.providers:
                continue
                
            try:
                provider_instance = self.providers[provider_type]
                provider_total = 0.0
                
                for script in scripts:
                    estimate = await provider_instance.estimate_cost(script, config)
                    provider_total += estimate.get("estimated_cost", 0.0)
                
                total_estimates[provider_type.value] = {
                    "total_cost": round(provider_total, 2),
                    "currency": "USD",
                    "video_count": len(scripts),
                    "average_per_video": round(provider_total / max(len(scripts), 1), 2),
                }
                
            except Exception as e:
                logger.warning(f"Failed to estimate cost for {provider_type.value}: {e}")
                continue
        
        return total_estimates
    
    def get_active_jobs(self) -> Dict[str, VideoGenerationJob]:
        """Get currently active video generation jobs."""
        return self.active_jobs.copy()
    
    def get_available_providers(self) -> List[VideoProvider]:
        """Get list of available video providers."""
        return list(self.providers.keys())
