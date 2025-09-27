"""
Base video provider interface.

Defines the contract that all video generation providers must implement.
This allows for easy integration of new AI video generation services.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass
from enum import Enum

from core.domain import Script, Video, VideoConfig, VideoProvider, ProcessingStatus


class VideoGenerationStatus(str, Enum):
    """Status of video generation job."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class VideoGenerationJob:
    """Represents a video generation job."""
    job_id: str
    provider: VideoProvider
    status: VideoGenerationStatus
    progress: float = 0.0  # 0-100
    estimated_completion: Optional[str] = None
    error_message: Optional[str] = None
    result_url: Optional[str] = None
    metadata: Dict[str, Any] = None


class BaseVideoProvider(ABC):
    """
    Abstract base class for video generation providers.
    
    All video providers must implement this interface to be compatible
    with the Paperclip video generation system.
    """
    
    def __init__(self, api_key: str, config: Dict[str, Any] = None):
        """Initialize provider with API credentials and configuration."""
        self.api_key = api_key
        self.config = config or {}
        self.provider_name = self._get_provider_name()
    
    @abstractmethod
    def _get_provider_name(self) -> VideoProvider:
        """Return the provider enum value."""
        pass
    
    @abstractmethod
    async def generate_video(self, script: Script, config: VideoConfig) -> VideoGenerationJob:
        """
        Start video generation from script.
        
        Args:
            script: Script entity with content and metadata
            config: Video generation configuration
            
        Returns:
            VideoGenerationJob with job details
        """
        pass
    
    @abstractmethod
    async def check_job_status(self, job_id: str) -> VideoGenerationJob:
        """
        Check the status of a video generation job.
        
        Args:
            job_id: Job identifier returned from generate_video
            
        Returns:
            Updated VideoGenerationJob
        """
        pass
    
    @abstractmethod
    async def download_video(self, job_id: str, output_path: str) -> Dict[str, Any]:
        """
        Download completed video to local storage.
        
        Args:
            job_id: Job identifier
            output_path: Local path to save video
            
        Returns:
            Video metadata (duration, size, format, etc.)
        """
        pass
    
    @abstractmethod
    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a video generation job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if cancellation was successful
        """
        pass
    
    async def get_supported_formats(self) -> Dict[str, Any]:
        """
        Get supported video formats and configurations.
        
        Returns:
            Dictionary of supported formats and their options
        """
        return {
            "formats": ["mp4"],
            "resolutions": ["1080p", "720p"],
            "aspect_ratios": ["16:9", "9:16", "1:1"],
            "max_duration": 300,  # seconds
        }
    
    async def estimate_cost(self, script: Script, config: VideoConfig) -> Dict[str, Any]:
        """
        Estimate the cost of generating video from script.
        
        Args:
            script: Script to generate video from
            config: Video configuration
            
        Returns:
            Cost estimate information
        """
        return {
            "estimated_cost": 0.0,
            "currency": "USD",
            "factors": ["duration", "quality", "complexity"],
            "note": "Cost estimation not implemented for this provider"
        }
    
    async def validate_script(self, script: Script) -> Dict[str, Any]:
        """
        Validate script compatibility with this provider.
        
        Args:
            script: Script to validate
            
        Returns:
            Validation results with any issues or warnings
        """
        issues = []
        warnings = []
        
        # Basic validation
        if not script.content:
            issues.append("Script has no content")
        
        if script.estimated_duration and script.estimated_duration > 10:  # 10 minutes
            warnings.append("Script duration may be too long for some providers")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
        }
    
    def _parse_script_scenes(self, script_content: str) -> list[Dict[str, Any]]:
        """Parse script content into individual scenes."""
        scenes = []
        
        # Split by scene separators
        raw_scenes = script_content.split("---")
        
        for i, scene_text in enumerate(raw_scenes):
            scene_text = scene_text.strip()
            if not scene_text:
                continue
            
            scene = self._parse_single_scene(scene_text, i + 1)
            if scene:
                scenes.append(scene)
        
        return scenes
    
    def _parse_single_scene(self, scene_text: str, scene_number: int) -> Optional[Dict[str, Any]]:
        """Parse a single scene from script text."""
        lines = scene_text.split('\n')
        
        scene = {
            "scene_number": scene_number,
            "title": "",
            "visual_description": "",
            "narration": "",
            "callouts": [],
            "duration_estimate": 0.0,
        }
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Scene title
            if line.startswith("#"):
                scene["title"] = line.lstrip("#").strip()
                # Extract duration if present
                if "(" in scene["title"] and "s)" in scene["title"]:
                    import re
                    duration_match = re.search(r'\((\d+\.?\d*)s\)', scene["title"])
                    if duration_match:
                        scene["duration_estimate"] = float(duration_match.group(1))
                        scene["title"] = re.sub(r'\s*\(\d+\.?\d*s\)', '', scene["title"])
            
            # Visual descriptions
            elif line.startswith("[") and line.endswith("]"):
                if "CALLOUT:" in line:
                    callout_text = line.replace("[CALLOUT:", "").replace("]", "").strip()
                    scene["callouts"].append(callout_text)
                else:
                    scene["visual_description"] += f"{line}\n"
            
            # Section headers
            elif line.startswith("**") and line.endswith("**"):
                section_name = line.strip("*").lower()
                if "narration" in section_name:
                    current_section = "narration"
                else:
                    current_section = None
            
            # Content lines
            else:
                if current_section == "narration":
                    scene["narration"] += f"{line} "
                elif not current_section and not scene["visual_description"]:
                    # Default to narration if no section specified
                    scene["narration"] += f"{line} "
        
        # Clean up
        scene["visual_description"] = scene["visual_description"].strip()
        scene["narration"] = scene["narration"].strip()
        
        # Estimate duration if not provided
        if scene["duration_estimate"] == 0.0:
            word_count = len(scene["narration"].split())
            scene["duration_estimate"] = max(5.0, (word_count / 150) * 60)  # Min 5 seconds
        
        return scene if (scene["title"] or scene["narration"]) else None
    
    def _build_generation_request(self, script: Script, config: VideoConfig) -> Dict[str, Any]:
        """Build provider-specific generation request."""
        scenes = self._parse_script_scenes(script.content)
        
        return {
            "script_id": str(script.id),
            "title": script.title,
            "scenes": scenes,
            "config": {
                "quality": config.quality,
                "aspect_ratio": config.aspect_ratio,
                "style": config.style,
                "include_narration": config.include_narration,
                "voice_style": config.voice_style,
                **config.settings,
            },
            "metadata": {
                "estimated_duration": script.estimated_duration,
                "scene_count": script.scene_count,
                "template": script.template.value,
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check provider health and availability."""
        return {
            "provider": self.provider_name.value,
            "status": "unknown",
            "message": "Health check not implemented",
            "last_checked": None,
        }
