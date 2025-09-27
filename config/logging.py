"""
Logging configuration for Paperclip.

Sets up structured logging with support for JSON and text formats,
file and console output, and integration with monitoring systems.
"""

import logging
import logging.config
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import structlog


def setup_logging(
    level: str = "INFO",
    format_type: str = "json",
    log_file: Optional[Path] = None,
    enable_colors: bool = True,
) -> None:
    """
    Setup application logging configuration.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Log format (json, text)
        log_file: Optional log file path
        enable_colors: Enable colored console output
    """
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info if format_type == "text" else structlog.processors.format_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            _get_renderer(format_type, enable_colors),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level.upper())
        ),
        logger_factory=structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    logging_config = _build_logging_config(level, format_type, log_file, enable_colors)
    logging.config.dictConfig(logging_config)
    
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Reduce noise from third-party libraries
    _configure_third_party_loggers()


def _get_renderer(format_type: str, enable_colors: bool):
    """Get the appropriate log renderer based on format type."""
    
    if format_type == "json":
        return structlog.processors.JSONRenderer()
    else:
        return structlog.dev.ConsoleRenderer(
            colors=enable_colors and sys.stderr.isatty()
        )


def _build_logging_config(
    level: str, 
    format_type: str, 
    log_file: Optional[Path], 
    enable_colors: bool
) -> Dict[str, Any]:
    """Build logging configuration dictionary."""
    
    # Formatters
    formatters = {
        "json": {
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
        },
        "text": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    }
    
    if enable_colors and format_type == "text":
        formatters["text"]["class"] = "colorlog.ColoredFormatter"
        formatters["text"]["format"] = (
            "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    # Handlers
    handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "level": level,
            "formatter": format_type,
            "stream": "ext://sys.stdout",
        },
    }
    
    # Add file handler if specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": level,
            "formatter": "json",  # Always use JSON for file logs
            "filename": str(log_file),
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 5,
            "encoding": "utf-8",
        }
    
    # Root logger configuration
    root_handlers = ["console"]
    if log_file:
        root_handlers.append("file")
    
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": formatters,
        "handlers": handlers,
        "root": {
            "level": level,
            "handlers": root_handlers,
        },
        "loggers": {
            "paperclip": {
                "level": level,
                "handlers": root_handlers,
                "propagate": False,
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": root_handlers,
                "propagate": False,
            },
            "fastapi": {
                "level": "INFO", 
                "handlers": root_handlers,
                "propagate": False,
            },
        },
    }


def _configure_third_party_loggers():
    """Configure third-party library loggers to reduce noise."""
    
    # Reduce noise from common libraries
    noisy_loggers = [
        "urllib3.connectionpool",
        "requests.packages.urllib3.connectionpool",
        "aiohttp.access",
        "multipart.multipart",
    ]
    
    for logger_name in noisy_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)
    
    # Set specific levels for important libraries
    logging.getLogger("surrealdb").setLevel(logging.INFO)
    logging.getLogger("openai").setLevel(logging.INFO)
    logging.getLogger("anthropic").setLevel(logging.INFO)


def get_logger(name: str = None) -> structlog.BoundLogger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (defaults to calling module)
        
    Returns:
        Configured structlog logger
    """
    if name is None:
        # Get the calling module name
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get("__name__", "paperclip")
    
    return structlog.get_logger(name)


class LoggingMiddleware:
    """
    FastAPI middleware for request/response logging.
    """
    
    def __init__(self, app):
        self.app = app
        self.logger = get_logger("paperclip.api")
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Extract request info
        request_info = {
            "method": scope["method"],
            "path": scope["path"],
            "query_string": scope["query_string"].decode(),
            "client": scope.get("client"),
        }
        
        # Log request start
        self.logger.info("Request started", **request_info)
        
        # Wrap send to capture response
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_code = message["status"]
                self.logger.info(
                    "Request completed",
                    status_code=status_code,
                    **request_info
                )
            await send(message)
        
        await self.app(scope, receive, send_wrapper)


# Context managers for structured logging
class LogContext:
    """Context manager for adding structured logging context."""
    
    def __init__(self, **context):
        self.context = context
        self.token = None
    
    def __enter__(self):
        self.token = structlog.contextvars.bind_contextvars(**self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.token:
            structlog.contextvars.reset_contextvars(**self.token)


def log_function_call(func_name: str = None):
    """Decorator to log function calls with parameters and results."""
    
    def decorator(func):
        import functools
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = get_logger()
            name = func_name or f"{func.__module__}.{func.__name__}"
            
            logger.debug("Function called", function=name, args=len(args), kwargs=list(kwargs.keys()))
            
            try:
                result = await func(*args, **kwargs)
                logger.debug("Function completed", function=name)
                return result
            except Exception as e:
                logger.error("Function failed", function=name, error=str(e))
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = get_logger()
            name = func_name or f"{func.__module__}.{func.__name__}"
            
            logger.debug("Function called", function=name, args=len(args), kwargs=list(kwargs.keys()))
            
            try:
                result = func(*args, **kwargs)
                logger.debug("Function completed", function=name)
                return result
            except Exception as e:
                logger.error("Function failed", function=name, error=str(e))
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
