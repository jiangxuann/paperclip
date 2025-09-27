"""
Video generation system for Paperclip.

This module provides an extensible framework for generating videos
from scripts using multiple AI providers and generation strategies.
"""

from .video import VideoGenerator
from .providers import (
    BaseVideoProvider,
    RunwayProvider,
    PikaProvider,
    LumaProvider,
    TemplateProvider,
)
from .templates import ScriptTemplateManager

__all__ = [
    "VideoGenerator",
    "BaseVideoProvider",
    "RunwayProvider", 
    "PikaProvider",
    "LumaProvider",
    "TemplateProvider",
    "ScriptTemplateManager",
]
