"""
Content processing pipeline for Paperclip.

This module orchestrates the transformation of PDF and URL content
into structured chapters and video scripts.
"""

from .pdf import PDFProcessor
from .url import URLProcessor
from .content import ContentAnalyzer, ChapterExtractor
from .script import ScriptGenerator
from .pipeline import ProcessingPipeline

__all__ = [
    "PDFProcessor",
    "URLProcessor", 
    "ContentAnalyzer",
    "ChapterExtractor",
    "ScriptGenerator",
    "ProcessingPipeline",
]
