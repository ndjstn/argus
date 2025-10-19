"""Custom exception classes for the agentic system"""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class AgenticError(Exception):
    """Base exception class for all agentic system errors"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, context: Optional[Dict[str, Any]] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        self.details = details
        
    def __str__(self):
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message

class DatabaseError(AgenticError):
    """Exception raised for database-related errors"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code or "DB_ERROR", context)

class RedisError(AgenticError):
    """Exception raised for Redis-related errors"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code or "REDIS_ERROR", context)

class APIError(AgenticError):
    """Exception raised for API-related errors"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code or "API_ERROR", context)

class ValidationError(AgenticError):
    """Exception raised for validation errors"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code or "VALIDATION_ERROR", context)

class ConfigurationError(AgenticError):
    """Exception raised for configuration errors"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code or "CONFIG_ERROR", context)

class ResourceError(AgenticError):
    """Exception raised for resource-related errors"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code or "RESOURCE_ERROR", context)

class FileIOError(AgenticError):
    """Exception raised for file I/O related errors"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code or "FILE_IO_ERROR", context)