"""
Unit tests for the ErrorRateLimiter and AdaptiveErrorRateLimiter classes.
"""

import pytest
import time
from unittest.mock import patch, Mock
from core.error_rate_limiter import (
    ErrorRateLimiter,
    AdaptiveErrorRateLimiter,
    initialize_rate_limiter,
    initialize_adaptive_rate_limiter,
    get_rate_limiter,
    get_adaptive_rate_limiter,
    is_error_logging_allowed
)


class TestErrorRateLimiter:
    """Test suite for ErrorRateLimiter class."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        limiter = ErrorRateLimiter()
        assert limiter.max_errors_per_second == 10
        assert limiter.max_errors_per_minute == 100
        assert limiter.window_size_seconds == 60

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        limiter = ErrorRateLimiter(
            max_errors_per_second=5,
            max_errors_per_minute=50,
            window_size_seconds=30
        )
        assert limiter.max_errors_per_second == 5
        assert limiter.max_errors_per_minute == 50
        assert limiter.window_size_seconds == 30

    def test_is_allowed_within_limits(self):
        """Test is_allowed when within limits."""
        limiter = ErrorRateLimiter(max_errors_per_second=5, max_errors_per_minute=10)
        
        # First 5 errors in a second should be allowed
        for i in range(5):
            assert limiter.is_allowed("test_error") is True
        
        # 6th error in the same second should be denied
        assert limiter.is_allowed("test_error") is False

    def test_is_allowed_exceeds_minute_limit(self):
        """Test is_allowed when exceeding minute limit."""
        limiter = ErrorRateLimiter(max_errors_per_second=100, max_errors_per_minute=5)
        
        # First 5 errors in a minute should be allowed
        for i in range(5):
            assert limiter.is_allowed("test_error") is True
        
        # 6th error in the same minute should be denied
        assert limiter.is_allowed("test_error") is False

    def test_is_allowed_different_error_types(self):
        """Test is_allowed with different error types."""
        limiter = ErrorRateLimiter(max_errors_per_second=2)
        
        # Should allow 2 errors of different types in the same second
        assert limiter.is_allowed("error_type_1") is True
        assert limiter.is_allowed("error_type_2") is True
        
        # 3rd error should be denied
        assert limiter.is_allowed("error_type_3") is False

    def test_get_stats(self):
        """Test get_stats method."""
        limiter = ErrorRateLimiter()
        
        # Initially stats should show zero counts
        stats = limiter.get_stats()
        assert stats["errors_in_current_second"] == 0
        assert stats["errors_in_current_minute"] == 0
        assert stats["max_errors_per_second"] == 10
        assert stats["max_errors_per_minute"] == 100
        assert stats["window_size_seconds"] == 60
        
        # After allowing an error, stats should update
        limiter.is_allowed("test_error")
        stats = limiter.get_stats()
        assert stats["errors_in_current_second"] == 1
        assert stats["errors_in_current_minute"] == 1


class TestAdaptiveErrorRateLimiter:
    """Test suite for AdaptiveErrorRateLimiter class."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        limiter = AdaptiveErrorRateLimiter()
        assert limiter.initial_max_errors_per_second == 10
        assert limiter.initial_max_errors_per_minute == 100
        assert limiter.window_size_seconds == 60
        assert limiter.adjustment_threshold == 0.8
        assert limiter.adjustment_factor == 1.5

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        limiter = AdaptiveErrorRateLimiter(
            initial_max_errors_per_second=5,
            initial_max_errors_per_minute=50,
            window_size_seconds=30,
            adjustment_threshold=0.9,
            adjustment_factor=2.0
        )
        assert limiter.initial_max_errors_per_second == 5
        assert limiter.initial_max_errors_per_minute == 50
        assert limiter.window_size_seconds == 30
        assert limiter.adjustment_threshold == 0.9
        assert limiter.adjustment_factor == 2.0

    def test_is_allowed_within_limits(self):
        """Test is_allowed when within limits."""
        limiter = AdaptiveErrorRateLimiter(max_errors_per_second=5, max_errors_per_minute=10)
        
        # First 5 errors in a second should be allowed
        for i in range(5):
            assert limiter.is_allowed("test_error") is True
        
        # 6th error in the same second should be denied
        assert limiter.is_allowed("test_error") is False

    def test_is_allowed_exceeds_minute_limit(self):
        """Test is_allowed when exceeding minute limit."""
        limiter = AdaptiveErrorRateLimiter(max_errors_per_second=100, max_errors_per_minute=5)
        
        # First 5 errors in a minute should be allowed
        for i in range(5):
            assert limiter.is_allowed("test_error") is True
        
        # 6th error in the same minute should be denied
        assert limiter.is_allowed("test_error") is False

    def test_get_stats(self):
        """Test get_stats method."""
        limiter = AdaptiveErrorRateLimiter()
        
        # Initially stats should show zero counts
        stats = limiter.get_stats()
        assert stats["errors_in_current_second"] == 0
        assert stats["errors_in_current_minute"] == 0
        assert stats["max_errors_per_second"] == 10
        assert stats["max_errors_per_minute"] == 100
        assert stats["window_size_seconds"] == 60
        
        # After allowing an error, stats should update
        limiter.is_allowed("test_error")
        stats = limiter.get_stats()
        assert stats["errors_in_current_second"] == 1
        assert stats["errors_in_current_minute"] == 1

    def test_get_error_type_stats(self):
        """Test get_error_type_stats method."""
        limiter = AdaptiveErrorRateLimiter()
        
        # Initially error type stats should be empty
        stats = limiter.get_error_type_stats()
        assert stats == {}
        
        # After allowing errors, stats should update
        limiter.is_allowed("error_type_1")
        limiter.is_allowed("error_type_1")
        limiter.is_allowed("error_type_2")
        
        stats = limiter.get_error_type_stats()
        assert stats["error_type_1"] == 2
        assert stats["error_type_2"] == 1


class TestGlobalRateLimiterFunctions:
    """Test suite for global rate limiter functions."""

    def test_initialize_and_get_rate_limiter(self):
        """Test initializing and getting the rate limiter."""
        # Initialize rate limiter
        initialize_rate_limiter(
            max_errors_per_second=5,
            max_errors_per_minute=50,
            window_size_seconds=30
        )
        
        # Get rate limiter
        limiter = get_rate_limiter()
        assert limiter is not None
        assert isinstance(limiter, ErrorRateLimiter)
        assert limiter.max_errors_per_second == 5
        assert limiter.max_errors_per_minute == 50
        assert limiter.window_size_seconds == 30

    def test_initialize_and_get_adaptive_rate_limiter(self):
        """Test initializing and getting the adaptive rate limiter."""
        # Initialize adaptive rate limiter
        initialize_adaptive_rate_limiter(
            initial_max_errors_per_second=5,
            initial_max_errors_per_minute=50,
            window_size_seconds=30,
            adjustment_threshold=0.9,
            adjustment_factor=2.0
        )
        
        # Get adaptive rate limiter
        limiter = get_adaptive_rate_limiter()
        assert limiter is not None
        assert isinstance(limiter, AdaptiveErrorRateLimiter)
        assert limiter.initial_max_errors_per_second == 5
        assert limiter.initial_max_errors_per_minute == 50
        assert limiter.window_size_seconds == 30
        assert limiter.adjustment_threshold == 0.9
        assert limiter.adjustment_factor == 2.0

    def test_is_error_logging_allowed_without_limiter(self):
        """Test is_error_logging_allowed when no limiter is configured."""
        # Reset global limiters
        global _rate_limiter, _adaptive_rate_limiter
        _rate_limiter = None
        _adaptive_rate_limiter = None
        
        # Should allow all errors when no limiter is configured
        assert is_error_logging_allowed("test_error") is True
        assert is_error_logging_allowed("test_error", use_adaptive=True) is True

    @patch('core.error_rate_limiter.get_rate_limiter')
    def test_is_error_logging_allowed_with_rate_limiter(self, mock_get_limiter):
        """Test is_error_logging_allowed with rate limiter."""
        # Configure mock limiter
        mock_limiter = Mock()
        mock_limiter.is_allowed.return_value = True
        mock_get_limiter.return_value = mock_limiter
        
        # Test with rate limiter
        result = is_error_logging_allowed("test_error")
        
        assert result is True
        mock_get_limiter.assert_called_once()
        mock_limiter.is_allowed.assert_called_once_with("test_error")

    @patch('core.error_rate_limiter.get_adaptive_rate_limiter')
    def test_is_error_logging_allowed_with_adaptive_rate_limiter(self, mock_get_limiter):
        """Test is_error_logging_allowed with adaptive rate limiter."""
        # Configure mock limiter
        mock_limiter = Mock()
        mock_limiter.is_allowed.return_value = True
        mock_get_limiter.return_value = mock_limiter
        
        # Test with adaptive rate limiter
        result = is_error_logging_allowed("test_error", use_adaptive=True)
        
        assert result is True
        mock_get_limiter.assert_called_once()
        mock_limiter.is_allowed.assert_called_once_with("test_error")