"""
Unit tests for the CentralizedErrorLogger class.
"""

import pytest
import os
import json
import tempfile
from core.error_logger import CentralizedErrorLogger, get_error_logger, log_error, log_error_event
from core.exceptions import AgenticError


class TestCentralizedErrorLogger:
    """Test suite for CentralizedErrorLogger class."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = CentralizedErrorLogger(log_dir=temp_dir)
            assert logger is not None
            assert os.path.exists(temp_dir)
            assert os.path.exists(os.path.join(temp_dir, "errors.log"))

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = CentralizedErrorLogger(
                log_dir=temp_dir,
                max_bytes=1024,
                backup_count=3
            )
            assert logger is not None
            assert logger.log_dir == temp_dir
            assert logger.max_bytes == 1024
            assert logger.backup_count == 3

    def test_log_error_with_exception(self):
        """Test logging an exception."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = CentralizedErrorLogger(log_dir=temp_dir)
            
            # Create a test exception
            try:
                raise ValueError("Test error")
            except ValueError as e:
                logger.log_error(e, {"test": "context"})
            
            # Check that the error was logged
            log_file = os.path.join(temp_dir, "errors.log")
            assert os.path.exists(log_file)
            
            with open(log_file, 'r') as f:
                content = f.read()
                assert "Test error" in content
                assert "test" in content
                assert "context" in content

    def test_log_error_with_agentic_error(self):
        """Test logging an AgenticError."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = CentralizedErrorLogger(log_dir=temp_dir)
            
            # Create a test AgenticError
            error = AgenticError(
                error_code="TEST_ERROR",
                message="Test Agentic error",
                details={"test": "details"}
            )
            logger.log_error(error, {"test": "context"})
            
            # Check that the error was logged
            log_file = os.path.join(temp_dir, "errors.log")
            assert os.path.exists(log_file)
            
            with open(log_file, 'r') as f:
                content = f.read()
                assert "Test Agentic error" in content
                assert "TEST_ERROR" in content
                assert "test" in content
                assert "context" in content
                assert "details" in content

    def test_log_error_event(self):
        """Test logging an error event."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = CentralizedErrorLogger(log_dir=temp_dir)
            
            logger.log_error_event("TEST_EVENT", "Test error message", {"test": "context"})
            
            # Check that the error was logged
            log_file = os.path.join(temp_dir, "errors.log")
            assert os.path.exists(log_file)
            
            with open(log_file, 'r') as f:
                content = f.read()
                assert "TEST_EVENT" in content
                assert "Test error message" in content
                assert "test" in content
                assert "context" in content

    def test_get_logger(self):
        """Test getting the underlying logger."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = CentralizedErrorLogger(log_dir=temp_dir)
            underlying_logger = logger.get_logger()
            assert underlying_logger is not None
            assert underlying_logger.name == "agentic_error_logger"


class TestGlobalErrorLoggerFunctions:
    """Test suite for global error logger functions."""

    def test_get_error_logger(self):
        """Test getting the global error logger."""
        logger = get_error_logger()
        assert logger is not None
        assert isinstance(logger, CentralizedErrorLogger)

    def test_log_error_function(self):
        """Test the global log_error function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a new logger for this test
            logger = CentralizedErrorLogger(log_dir=temp_dir)
            
            # Patch the global logger to use our test logger
            import core.error_logger
            original_logger = core.error_logger._error_logger
            core.error_logger._error_logger = logger
            
            try:
                # Log an error
                try:
                    raise RuntimeError("Global test error")
                except RuntimeError as e:
                    log_error(e, {"global": "test"})
                
                # Check that the error was logged
                log_file = os.path.join(temp_dir, "errors.log")
                assert os.path.exists(log_file)
                
                with open(log_file, 'r') as f:
                    content = f.read()
                    assert "Global test error" in content
                    assert "global" in content
                    assert "test" in content
            finally:
                # Restore the original logger
                core.error_logger._error_logger = original_logger

    def test_log_error_event_function(self):
        """Test the global log_error_event function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a new logger for this test
            logger = CentralizedErrorLogger(log_dir=temp_dir)
            
            # Patch the global logger to use our test logger
            import core.error_logger
            original_logger = core.error_logger._error_logger
            core.error_logger._error_logger = logger
            
            try:
                # Log an error event
                log_error_event("GLOBAL_TEST_EVENT", "Global test error message", {"global": "test"})
                
                # Check that the error was logged
                log_file = os.path.join(temp_dir, "errors.log")
                assert os.path.exists(log_file)
                
                with open(log_file, 'r') as f:
                    content = f.read()
                    assert "GLOBAL_TEST_EVENT" in content
                    assert "Global test error message" in content
                    assert "global" in content
                    assert "test" in content
            finally:
                # Restore the original logger
                core.error_logger._error_logger = original_logger