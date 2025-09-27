"""
Celery worker configuration for Paperclip.

This module configures the Celery application for background task processing.
"""

import os
from celery import Celery
from config import get_settings

# Get settings
settings = get_settings()

# Create Celery app
celery = Celery(
    "paperclip",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["core.tasks"]  # Include task modules
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "core.tasks.process_document": {"queue": "document_processing"},
        "core.tasks.generate_script": {"queue": "script_generation"},
        "core.tasks.generate_video": {"queue": "video_generation"},
    },
)


def main():
    """Main entry point for the worker."""
    celery.start()


if __name__ == "__main__":
    main()