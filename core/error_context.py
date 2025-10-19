"""
Error context management for the agentic system.
"""

import contextvars
import uuid
from typing import Dict, Any, Optional
from contextlib import contextmanager


# Context variable to store the current error context
_error_context: contextvars.ContextVar[Dict[str, Any]] = contextvars.ContextVar('error_context', default={})


class ErrorContextManager:
    """Manager for error context propagation across services."""
    
    @staticmethod
    def get_context() -> Dict[str, Any]:
        """
        Get the current error context.
        
        Returns:
            The current error context
        """
        return _error_context.get().copy()
    
    @staticmethod
    def set_context(context: Dict[str, Any]) -> None:
        """
        Set the error context.
        
        Args:
            context: The error context to set
        """
        _error_context.set(context)
    
    @staticmethod
    def update_context(updates: Dict[str, Any]) -> None:
        """
        Update the error context with new values.
        
        Args:
            updates: The updates to apply to the error context
        """
        current_context = _error_context.get()
        current_context.update(updates)
        _error_context.set(current_context)
    
    @staticmethod
    def clear_context() -> None:
        """Clear the error context."""
        _error_context.set({})
    
    @staticmethod
    def get_request_id() -> Optional[str]:
        """
        Get the request ID from the error context.
        
        Returns:
            The request ID, or None if not set
        """
        context = _error_context.get()
        return context.get('request_id')
    
    @staticmethod
    def set_request_id(request_id: Optional[str] = None) -> str:
        """
        Set the request ID in the error context.
        
        Args:
            request_id: The request ID to set, or None to generate a new one
            
        Returns:
            The request ID that was set
        """
        if request_id is None:
            request_id = str(uuid.uuid4())
        
        ErrorContextManager.set_context({'request_id': request_id})
        return request_id


@contextmanager
def error_context(request_id: Optional[str] = None, **kwargs):
    """
    Context manager for error context propagation.
    
    Args:
        request_id: The request ID, or None to generate a new one
        **kwargs: Additional context to set
    """
    # Save the current context
    current_context = ErrorContextManager.get_context().copy()
    
    try:
        # Create new context with request ID
        new_context = {'request_id': ErrorContextManager.set_request_id(request_id)}
        new_context.update(kwargs)
        ErrorContextManager.set_context(new_context)
        
        yield new_context
    finally:
        # Restore the previous context
        ErrorContextManager.set_context(current_context)


def get_current_context() -> Dict[str, Any]:
    """
    Get the current error context.
    
    Returns:
        The current error context
    """
    return ErrorContextManager.get_context()


def get_request_id() -> Optional[str]:
    """
    Get the current request ID.
    
    Returns:
        The current request ID, or None if not set
    """
    return ErrorContextManager.get_request_id()


def add_context_to_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> Exception:
    """
    Add context information to an error.
    
    Args:
        error: The error to add context to
        context: Additional context to add
        
    Returns:
        The error with added context
    """
    # Get the current context
    current_context = ErrorContextManager.get_context()
    
    # Add provided context if any
    if context:
        current_context.update(context)
    
    # Add context to error if it has a __dict__ attribute
    if hasattr(error, '__dict__'):
        if not hasattr(error, 'context'):
            error.context = {}
        error.context.update(current_context)
    
    return error