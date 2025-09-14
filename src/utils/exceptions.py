"""
Custom exception classes for the application
"""

class DisposisiException(Exception):
    """Base exception for the application"""
    def __init__(self, message: str, code: str = None, details: dict = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

class DatabaseError(DisposisiException):
    """Database-related errors"""
    pass

class ValidationError(DisposisiException):
    """Input validation errors"""
    pass

class AuthenticationError(DisposisiException):
    """Authentication and authorization errors"""
    pass

class FileError(DisposisiException):
    """File operation errors"""
    pass

class ConfigurationError(DisposisiException):
    """Configuration-related errors"""
    pass

class APIError(DisposisiException):
    """API-related errors"""
    pass

class WorkflowError(DisposisiException):
    """Document workflow errors"""
    pass

class BackupError(DisposisiException):
    """Backup and restore errors"""
    pass

class NotificationError(DisposisiException):
    """Notification system errors"""
    pass