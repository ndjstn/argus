"""
Unit tests for the error recovery mechanisms.
"""

import pytest
import time
import random
from unittest.mock import Mock, patch
from core.error_recovery import (
    ErrorRecoveryStrategy,
    ExponentialBackoffStrategy,
    CircuitBreaker,
    CircuitBreakerError,
    ValidationError,
    ConfigurationError,
    retry_with_backoff,
    with_circuit_breaker,
    AgenticError,
    DatabaseError,
    RedisError,
    APIError,
    FileIOError
)


class TestExponentialBackoffStrategy:
    """Test suite for ExponentialBackoffStrategy class."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        strategy = ExponentialBackoffStrategy("test")
        assert strategy.name == "test"
        assert strategy.base_delay == 1.0
        assert strategy.max_delay == 60.0
        assert strategy.multiplier == 2.0
        assert strategy.jitter is True

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        strategy = ExponentialBackoffStrategy(
            name="custom",
            base_delay=2.0,
            max_delay=30.0,
            multiplier=3.0,
            jitter=False
        )
        assert strategy.name == "custom"
        assert strategy.base_delay == 2.0
        assert strategy.max_delay == 30.0
        assert strategy.multiplier == 3.0
        assert strategy.jitter is False

    def test_should_retry_with_agentic_error(self):
        """Test should_retry with AgenticError."""
        strategy = ExponentialBackoffStrategy("test")
        
        # Test with a generic AgenticError (should retry)
        error = AgenticError("TEST_ERROR", "Test error")
        assert strategy.should_retry(error, 1) is True
        
        # Test with ValidationError (should not retry)
        error = ValidationError("Validation error")
        assert strategy.should_retry(error, 1) is False
        
        # Test with ConfigurationError (should not retry)
        error = ConfigurationError("Configuration error")
        assert strategy.should_retry(error, 1) is False

    def test_should_retry_with_transient_errors(self):
        """Test should_retry with transient errors."""
        strategy = ExponentialBackoffStrategy("test")
        
        # Test with DatabaseError (should retry)
        error = DatabaseError("Database error")
        assert strategy.should_retry(error, 1) is True
        
        # Test with RedisError (should retry)
        error = RedisError("Redis error")
        assert strategy.should_retry(error, 1) is True
        
        # Test with APIError (should retry)
        error = APIError("API error")
        assert strategy.should_retry(error, 1) is True
        
        # Test with FileIOError (should retry)
        error = FileIOError("File I/O error")
        assert strategy.should_retry(error, 1) is True
        
        # Test with ConnectionError (should retry)
        error = ConnectionError("Connection error")
        assert strategy.should_retry(error, 1) is True
        
        # Test with TimeoutError (should retry)
        error = TimeoutError("Timeout error")
        assert strategy.should_retry(error, 1) is True

    def test_should_retry_with_permanent_error(self):
        """Test should_retry with permanent error."""
        strategy = ExponentialBackoffStrategy("test")
        
        # Test with ValueError (should not retry)
        error = ValueError("Value error")
        assert strategy.should_retry(error, 1) is False

    def test_get_delay_without_jitter(self):
        """Test get_delay without jitter."""
        strategy = ExponentialBackoffStrategy(
            name="test",
            base_delay=1.0,
            max_delay=10.0,
            multiplier=2.0,
            jitter=False
        )
        
        # Test first attempt
        delay = strategy.get_delay(1)
        assert delay == 1.0
        
        # Test second attempt
        delay = strategy.get_delay(2)
        assert delay == 2.0
        
        # Test third attempt (should be capped at max_delay)
        delay = strategy.get_delay(5)
        assert delay == 10.0

    def test_get_delay_with_jitter(self):
        """Test get_delay with jitter."""
        strategy = ExponentialBackoffStrategy(
            name="test",
            base_delay=1.0,
            max_delay=10.0,
            multiplier=2.0,
            jitter=True
        )
        
        # Test that delay is within expected range with jitter
        for attempt in range(1, 6):
            delay = strategy.get_delay(attempt)
            expected_max = min(1.0 * (2.0 ** (attempt - 1)), 10.0)
            assert 0.5 * expected_max <= delay <= expected_max


class TestCircuitBreaker:
    """Test suite for CircuitBreaker class."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        cb = CircuitBreaker("test")
        assert cb.name == "test"
        assert cb.failure_threshold == 5
        assert cb.recovery_timeout == 60.0
        assert cb.expected_exception == Exception
        assert cb.failure_count == 0
        assert cb.last_failure_time is None
        assert cb.state == "CLOSED"

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        cb = CircuitBreaker(
            name="custom",
            failure_threshold=3,
            recovery_timeout=30.0,
            expected_exception=ValueError
        )
        assert cb.name == "custom"
        assert cb.failure_threshold == 3
        assert cb.recovery_timeout == 30.0
        assert cb.expected_exception == ValueError

    def test_call_success(self):
        """Test successful function call."""
        cb = CircuitBreaker("test")
        
        def success_func():
            return "success"
        
        result = cb.call(success_func)
        assert result == "success"
        assert cb.failure_count == 0
        assert cb.state == "CLOSED"

    def test_call_failure_below_threshold(self):
        """Test function call failure below threshold."""
        cb = CircuitBreaker("test", failure_threshold=3)
        
        def fail_func():
            raise ValueError("Test failure")
        
        # First failure
        with pytest.raises(ValueError):
            cb.call(fail_func)
        assert cb.failure_count == 1
        assert cb.state == "CLOSED"
        
        # Second failure
        with pytest.raises(ValueError):
            cb.call(fail_func)
        assert cb.failure_count == 2
        assert cb.state == "CLOSED"

    def test_call_failure_above_threshold(self):
        """Test function call failure above threshold."""
        cb = CircuitBreaker("test", failure_threshold=2)
        
        def fail_func():
            raise ValueError("Test failure")
        
        # First failure
        with pytest.raises(ValueError):
            cb.call(fail_func)
        assert cb.failure_count == 1
        assert cb.state == "CLOSED"
        
        # Second failure (should open circuit)
        with pytest.raises(ValueError):
            cb.call(fail_func)
        assert cb.failure_count == 2
        assert cb.state == "OPEN"

    def test_call_when_circuit_open(self):
        """Test function call when circuit is open."""
        cb = CircuitBreaker("test")
        cb.state = "OPEN"
        
        def success_func():
            return "success"
        
        with pytest.raises(CircuitBreakerError):
            cb.call(success_func)

    def test_call_when_circuit_half_open(self):
        """Test function call when circuit is half-open."""
        cb = CircuitBreaker("test")
        cb.state = "HALF_OPEN"
        
        # Successful call should close circuit
        def success_func():
            return "success"
        
        result = cb.call(success_func)
        assert result == "success"
        assert cb.state == "CLOSED"
        assert cb.failure_count == 0

    def test_call_failure_when_circuit_half_open(self):
        """Test function call failure when circuit is half-open."""
        cb = CircuitBreaker("test")
        cb.state = "HALF_OPEN"
        
        # Failed call should open circuit again
        def fail_func():
            raise ValueError("Test failure")
        
        with pytest.raises(ValueError):
            cb.call(fail_func)
        assert cb.state == "OPEN"


class TestRetryDecorator:
    """Test suite for retry_with_backoff decorator."""

    def test_retry_success_on_first_attempt(self):
        """Test retry with success on first attempt."""
        call_count = 0
        
        @retry_with_backoff(max_attempts=3)
        def success_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = success_func()
        assert result == "success"
        assert call_count == 1

    def test_retry_success_on_second_attempt(self):
        """Test retry with success on second attempt."""
        call_count = 0
        
        @retry_with_backoff(max_attempts=3)
        def sometimes_fail_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise DatabaseError("Temporary database error")
            return "success"
        
        result = sometimes_fail_func()
        assert result == "success"
        assert call_count == 2

    def test_retry_exhausted_attempts(self):
        """Test retry with exhausted attempts."""
        call_count = 0
        
        @retry_with_backoff(max_attempts=3)
        def always_fail_func():
            nonlocal call_count
            call_count += 1
            raise DatabaseError("Persistent database error")
        
        with pytest.raises(DatabaseError):
            always_fail_func()
        assert call_count == 3

    def test_retry_with_on_retry_callback(self):
        """Test retry with on_retry callback."""
        call_count = 0
        retry_callback_count = 0
        
        def on_retry_callback(error, attempt):
            nonlocal retry_callback_count
            retry_callback_count += 1
            assert isinstance(error, DatabaseError)
            assert attempt >= 1
        
        @retry_with_backoff(max_attempts=3, on_retry=on_retry_callback)
        def fail_func():
            nonlocal call_count
            call_count += 1
            raise DatabaseError("Test error")
        
        with pytest.raises(DatabaseError):
            fail_func()
        assert call_count == 3
        assert retry_callback_count == 2  # Called on attempts 1 and 2


class TestCircuitBreakerDecorator:
    """Test suite for with_circuit_breaker decorator."""

    def test_circuit_breaker_success(self):
        """Test circuit breaker with successful function calls."""
        cb = CircuitBreaker("test")
        
        @with_circuit_breaker(cb)
        def success_func():
            return "success"
        
        result = success_func()
        assert result == "success"
        assert cb.failure_count == 0
        assert cb.state == "CLOSED"

    def test_circuit_breaker_failure(self):
        """Test circuit breaker with failed function calls."""
        cb = CircuitBreaker("test", failure_threshold=2)
        
        @with_circuit_breaker(cb)
        def fail_func():
            raise ValueError("Test failure")
        
        # First failure
        with pytest.raises(ValueError):
            fail_func()
        assert cb.failure_count == 1
        assert cb.state == "CLOSED"
        
        # Second failure (should open circuit)
        with pytest.raises(ValueError):
            fail_func()
        assert cb.failure_count == 2
        assert cb.state == "OPEN"
        
        # Third call (should raise CircuitBreakerError)
        with pytest.raises(CircuitBreakerError):
            fail_func()


class TestCustomExceptions:
    """Test suite for custom exception classes."""

    def test_circuit_breaker_error(self):
        """Test CircuitBreakerError."""
        error = CircuitBreakerError("Circuit breaker is open")
        assert error.error_code == "CIRCUIT_BREAKER_OPEN"
        assert error.message == "Circuit breaker is open"

    def test_validation_error(self):
        """Test ValidationError."""
        error = ValidationError("Invalid input")
        assert error.error_code == "VALIDATION_ERROR"
        assert error.message == "Invalid input"
        assert error.details is None
        
        # Test with details
        details = {"field": "value"}
        error = ValidationError("Invalid input", details)
        assert error.details == details

    def test_configuration_error(self):
        """Test ConfigurationError."""
        error = ConfigurationError("Invalid configuration")
        assert error.error_code == "CONFIGURATION_ERROR"
        assert error.message == "Invalid configuration"
        assert error.details is None
        
        # Test with details
        details = {"config_key": "invalid_value"}
        error = ConfigurationError("Invalid configuration", details)
        assert error.details == details