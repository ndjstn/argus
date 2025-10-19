"""
Unit tests for the ErrorContextManager class and related functions.
"""

import pytest
import uuid
from core.error_context import (
    ErrorContextManager, 
    error_context, 
    get_current_context, 
    get_request_id,
    add_context_to_error
)


class TestErrorContextManager:
    """Test suite for ErrorContextManager class."""

    def test_get_context_default(self):
        """Test getting the default context."""
        # Clear context first
        ErrorContextManager.clear_context()
        
        context = ErrorContextManager.get_context()
        assert isinstance(context, dict)
        assert len(context) == 0

    def test_set_context(self):
        """Test setting the context."""
        test_context = {"test": "value", "number": 42}
        ErrorContextManager.set_context(test_context)
        
        context = ErrorContextManager.get_context()
        assert context == test_context

    def test_update_context(self):
        """Test updating the context."""
        # Set initial context
        initial_context = {"test": "value", "number": 42}
        ErrorContextManager.set_context(initial_context)
        
        # Update context
        updates = {"test": "updated", "new_key": "new_value"}
        ErrorContextManager.update_context(updates)
        
        # Check updated context
        context = ErrorContextManager.get_context()
        assert context["test"] == "updated"
        assert context["number"] == 42
        assert context["new_key"] == "new_value"

    def test_clear_context(self):
        """Test clearing the context."""
        # Set context
        test_context = {"test": "value"}
        ErrorContextManager.set_context(test_context)
        
        # Clear context
        ErrorContextManager.clear_context()
        
        # Check context is empty
        context = ErrorContextManager.get_context()
        assert len(context) == 0

    def test_get_request_id_when_not_set(self):
        """Test getting request ID when not set."""
        # Clear context first
        ErrorContextManager.clear_context()
        
        request_id = ErrorContextManager.get_request_id()
        assert request_id is None

    def test_set_request_id_with_value(self):
        """Test setting request ID with a specific value."""
        test_request_id = str(uuid.uuid4())
        returned_id = ErrorContextManager.set_request_id(test_request_id)
        
        assert returned_id == test_request_id
        assert ErrorContextManager.get_request_id() == test_request_id

    def test_set_request_id_without_value(self):
        """Test setting request ID without a specific value."""
        returned_id = ErrorContextManager.set_request_id()
        
        assert returned_id is not None
        assert isinstance(returned_id, str)
        assert len(returned_id) > 0
        assert ErrorContextManager.get_request_id() == returned_id


class TestErrorContextFunction:
    """Test suite for error_context function."""

    def test_error_context_with_request_id(self):
        """Test error_context with a specific request ID."""
        test_request_id = str(uuid.uuid4())
        
        with error_context(request_id=test_request_id) as context:
            assert context["request_id"] == test_request_id
            assert get_request_id() == test_request_id
            assert get_current_context() == context

    def test_error_context_without_request_id(self):
        """Test error_context without a specific request ID."""
        with error_context() as context:
            assert context["request_id"] is not None
            assert isinstance(context["request_id"], str)
            assert len(context["request_id"]) > 0
            assert get_request_id() == context["request_id"]
            assert get_current_context() == context

    def test_error_context_with_additional_context(self):
        """Test error_context with additional context."""
        test_request_id = str(uuid.uuid4())
        additional_context = {"user_id": "123", "session_id": "abc"}
        
        with error_context(request_id=test_request_id, **additional_context) as context:
            assert context["request_id"] == test_request_id
            assert context["user_id"] == "123"
            assert context["session_id"] == "abc"
            assert get_current_context() == context

    def test_error_context_restores_previous_context(self):
        """Test that error_context restores the previous context."""
        # Set initial context
        initial_context = {"test": "initial"}
        ErrorContextManager.set_context(initial_context)
        
        # Use error_context
        with error_context() as new_context:
            assert get_current_context() == new_context
            assert new_context["request_id"] is not None
        
        # Check that previous context is restored
        current_context = get_current_context()
        assert current_context == initial_context


class TestAddContextToError:
    """Test suite for add_context_to_error function."""

    def test_add_context_to_error_without_existing_context(self):
        """Test adding context to an error without existing context."""
        # Clear context first
        ErrorContextManager.clear_context()
        
        # Set some context
        ErrorContextManager.set_context({"test": "value"})
        
        # Create an error and add context
        error = ValueError("Test error")
        error_with_context = add_context_to_error(error)
        
        # Check that context was added
        assert hasattr(error_with_context, 'context')
        assert error_with_context.context["test"] == "value"

    def test_add_context_to_error_with_existing_context(self):
        """Test adding context to an error with existing context."""
        # Clear context first
        ErrorContextManager.clear_context()
        
        # Set some context
        ErrorContextManager.set_context({"test": "value"})
        
        # Create an error with existing context
        error = ValueError("Test error")
        error.context = {"existing": "context"}
        
        # Add more context
        error_with_context = add_context_to_error(error)
        
        # Check that context was added
        assert error_with_context.context["existing"] == "context"
        assert error_with_context.context["test"] == "value"

    def test_add_context_to_error_with_additional_context(self):
        """Test adding additional context to an error."""
        # Clear context first
        ErrorContextManager.clear_context()
        
        # Set some context
        ErrorContextManager.set_context({"test": "value"})
        
        # Create an error and add additional context
        error = ValueError("Test error")
        additional_context = {"additional": "info"}
        error_with_context = add_context_to_error(error, additional_context)
        
        # Check that context was added
        assert hasattr(error_with_context, 'context')
        assert error_with_context.context["test"] == "value"
        assert error_with_context.context["additional"] == "info"

    def test_add_context_to_error_with_non_dict_error(self):
        """Test adding context to an error that doesn't support __dict__."""
        # Clear context first
        ErrorContextManager.clear_context()
        
        # Set some context
        ErrorContextManager.set_context({"test": "value"})
        
        # Create an error that doesn't support __dict__ (this is a bit contrived)
        class SimpleError:
            def __init__(self, message):
                self.message = message
        
        error = SimpleError("Test error")
        error_with_context = add_context_to_error(error)
        
        # For errors without __dict__, the function should return the error unchanged
        assert error_with_context is error