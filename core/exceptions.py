"""
Custom exceptions for Paperclip.

Defines application-specific exceptions with clear error messages
and appropriate HTTP status codes for API responses.
"""


class PaperclipError(Exception):
    """Base exception for all Paperclip errors."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ProcessingError(PaperclipError):
    """Raised when content processing fails."""
    pass


class ValidationError(PaperclipError):
    """Raised when input validation fails."""
    pass


class ConfigurationError(PaperclipError):
    """Raised when configuration is invalid."""
    pass


class DatabaseError(PaperclipError):
    """Raised when database operations fail."""
    pass


class ExternalServiceError(PaperclipError):
    """Raised when external service calls fail."""
    
    def __init__(self, message: str, service_name: str, status_code: int = None, details: dict = None):
        super().__init__(message, details)
        self.service_name = service_name
        self.status_code = status_code


class AuthenticationError(PaperclipError):
    """Raised when authentication fails."""
    pass


class AuthorizationError(PaperclipError):
    """Raised when authorization fails."""
    pass


class NotFoundError(PaperclipError):
    """Raised when a requested resource is not found."""
    pass


class ConflictError(PaperclipError):
    """Raised when a resource conflict occurs."""
    pass
