"""
FastAPI backend for Paperclip.

Provides REST API endpoints for managing projects, content sources,
scripts, and video generation.
"""

from .main import app
from .dependencies import get_settings, get_database

__all__ = ["app", "get_settings", "get_database"]
