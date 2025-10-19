"""
Centralized error logging service for the agentic system.
"""

import logging
import logging.handlers
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from .exceptions import AgenticError


class CentralizedErrorLogger:
    """Centralized error logging service."""
    
    def __init__(self, log_dir: str = "logs", max_bytes: int = 10485760, backup_count: int = 5):
        """
        Initialize the centralized error logger.
        
        Args:
            log_dir: Directory to store log files
            max_bytes: Maximum size of log file before rotation
            backup_count: Number of backup files to keep
        """
        self.log_dir = log_dir
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        
        # Create log directory if it doesn't exist
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Set up the centralized error logger
        self.logger = logging.getLogger("agentic_error_logger")
        self.logger.setLevel(logging.ERROR)
        
        # Remove existing handlers to avoid duplicates
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create file handler with rotation
        log_file = os.path.join(self.log_dir, "errors.log")
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count
        )
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        self.logger.addHandler(file_handler)
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """
        Log an error with context information.
        
        Args:
            error: The exception to log
            context: Additional context information
        """
        # Create error record
        error_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {}
        }
        
        # Add traceback information if available
        if hasattr(error, '__traceback__'):
            import traceback
            error_record["traceback"] = traceback.format_tb(error.__traceback__)
        
        # Add error code if it's an AgenticError
        if isinstance(error, AgenticError):
            error_record["error_code"] = error.error_code
            error_record["details"] = error.details
        
        # Log the error
        self.logger.error(json.dumps(error_record, indent=2))
    
    def log_error_event(self, event: str, message: str, context: Optional[Dict[str, Any]] = None):
        """
        Log a specific error event.
        
        Args:
            event: The error event name
            message: The error message
            context: Additional context information
        """
        error_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event,
            "message": message,
            "context": context or {}
        }
        
        self.logger.error(json.dumps(error_record, indent=2))
    
    def get_logger(self) -> logging.Logger:
        """
        Get the underlying logger instance.
        
        Returns:
            The logger instance
        """
        return self.logger


# Global instance
_error_logger: Optional[CentralizedErrorLogger] = None


def get_error_logger() -> CentralizedErrorLogger:
    """
    Get the global centralized error logger instance.
    
    Returns:
        The centralized error logger instance
    """
    global _error_logger
    if _error_logger is None:
        _error_logger = CentralizedErrorLogger()
    return _error_logger


def log_error(error: Exception, context: Optional[Dict[str, Any]] = None):
    """
    Log an error using the global error logger.
    
    Args:
        error: The exception to log
        context: Additional context information
    """
    logger = get_error_logger()
    logger.log_error(error, context)


def log_error_event(event: str, message: str, context: Optional[Dict[str, Any]] = None):
    """
    Log a specific error event using the global error logger.
    
    Args:
        event: The error event name
        message: The error message
        context: Additional context information
    """
    logger = get_error_logger()
    logger.log_error_event(event, message, context)