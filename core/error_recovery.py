"""
Error recovery mechanisms for the agentic system.
"""

import time
import random
import logging
from typing import Callable, Any, Optional, Tuple, Dict
from functools import wraps
from .exceptions import AgenticError, DatabaseError, RedisError, APIError, FileIOError


class ErrorRecoveryStrategy:
    """Base class for error recovery strategies."""
    
    def __init__(self, name: str):
        """
        Initialize the error recovery strategy.
        
        Args:
            name: The name of the strategy
        """
        self.name = name
        self.logger = logging.getLogger(f"error_recovery.{name}")
    
    def should_retry(self, error: Exception, attempt: int) -> bool:
        """
        Determine if an operation should be retried based on the error and attempt number.
        
        Args:
            error: The error that occurred
            attempt: The current attempt number
            
        Returns:
            True if the operation should be retried, False otherwise
        """
        raise NotImplementedError
    
    def get_delay(self, attempt: int) -> float:
        """
        Get the delay before the next retry attempt.
        
        Args:
            attempt: The current attempt number
            
        Returns:
            The delay in seconds
        """
        raise NotImplementedError


class ValidationError(AgenticError):
    """Exception raised for validation errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize the validation error.
        
        Args:
            message: The error message
            details: Additional details about the error
        """
        super().__init__(message, "VALIDATION_ERROR", None, details)


class ConfigurationError(AgenticError):
    """Exception raised for configuration errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize the configuration error.
        
        Args:
            message: The error message
            details: Additional details about the error
        """
        super().__init__(message, "CONFIGURATION_ERROR", None, details)


class ExponentialBackoffStrategy(ErrorRecoveryStrategy):
    """Error recovery strategy using exponential backoff with jitter."""
    
    def __init__(
        self,
        name: str = "exponential_backoff",
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        multiplier: float = 2.0,
        jitter: bool = True
    ):
        """
        Initialize the exponential backoff strategy.
        
        Args:
            name: The name of the strategy
            base_delay: The base delay in seconds
            max_delay: The maximum delay in seconds
            multiplier: The multiplier for exponential backoff
            jitter: Whether to add jitter to the delay
        """
        super().__init__(name)
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.multiplier = multiplier
        self.jitter = jitter
    
    def should_retry(self, error: Exception, attempt: int) -> bool:
        """
        Determine if an operation should be retried.
        
        Args:
            error: The error that occurred
            attempt: The current attempt number
            
        Returns:
            True if the operation should be retried, False otherwise
        """
        # Retry on any AgenticError except those that indicate a permanent failure
        if isinstance(error, AgenticError):
            # Don't retry on validation errors or configuration errors
            if isinstance(error, (ValidationError, ConfigurationError)):
                return False
            return True
        
        # Retry on common transient errors
        transient_errors = (
            DatabaseError,
            RedisError,
            APIError,
            FileIOError,
            ConnectionError,
            TimeoutError
        )
        
        return isinstance(error, transient_errors)
    
    def get_delay(self, attempt: int) -> float:
        """
        Get the delay before the next retry attempt using exponential backoff with jitter.
        
        Args:
            attempt: The current attempt number
            
        Returns:
            The delay in seconds
        """
        # Calculate exponential backoff delay
        delay = min(self.base_delay * (self.multiplier ** (attempt - 1)), self.max_delay)
        
        # Add jitter if enabled
        if self.jitter:
            delay *= (0.5 + random.random() * 0.5)
        
        return delay


class CircuitBreaker:
    """Circuit breaker pattern implementation for error recovery."""
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception
    ):
        """
        Initialize the circuit breaker.
        
        Args:
            name: The name of the circuit breaker
            failure_threshold: The number of failures before opening the circuit
            recovery_timeout: The timeout in seconds before attempting to close the circuit
            expected_exception: The type of exception to count as a failure
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.logger = logging.getLogger(f"circuit_breaker.{name}")
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Call a function with circuit breaker protection.
        
        Args:
            func: The function to call
            *args: Positional arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            The result of the function call
            
        Raises:
            The exception raised by the function, or CircuitBreakerError if the circuit is open
        """
        if self.state == "OPEN":
            if self.last_failure_time and time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = "HALF_OPEN"
                self.logger.info(f"Circuit breaker {self.name} is half-open")
            else:
                raise CircuitBreakerError(f"Circuit breaker {self.name} is open")
        
        try:
            result = func(*args, **kwargs)
            
            # Success - reset failure count and close circuit
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.logger.info(f"Circuit breaker {self.name} is closed")
            self.failure_count = 0
            return result
        except self.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            # Check if we should open the circuit
            if self.failure_count >= self.failure_threshold or self.state == "HALF_OPEN":
                self.state = "OPEN"
                self.logger.warning(f"Circuit breaker {self.name} is open due to {self.failure_count} failures")
            
            raise e


class CircuitBreakerError(AgenticError):
    """Exception raised when a circuit breaker is open."""
    
    def __init__(self, message: str):
        """
        Initialize the circuit breaker error.
        
        Args:
            message: The error message
        """
        super().__init__(message, "CIRCUIT_BREAKER_OPEN")




def retry_with_backoff(
    strategy: Optional[ErrorRecoveryStrategy] = None,
    max_attempts: int = 3,
    on_retry: Optional[Callable[[Exception, int], None]] = None
):
    """
    Decorator to retry a function with exponential backoff.
    
    Args:
        strategy: The error recovery strategy to use
        max_attempts: The maximum number of attempts
        on_retry: A callback function to call on each retry
        
    Returns:
        The decorated function
    """
    if strategy is None:
        strategy = ExponentialBackoffStrategy()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_error = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    
                    # Check if we should retry
                    if attempt < max_attempts and strategy.should_retry(e, attempt):
                        # Call retry callback if provided
                        if on_retry:
                            on_retry(e, attempt)
                        
                        # Calculate delay
                        delay = strategy.get_delay(attempt)
                        
                        # Log retry attempt
                        logging.getLogger("retry").info(
                            f"Retrying {func.__name__} (attempt {attempt}/{max_attempts}) "
                            f"after {delay:.2f}s delay due to {type(e).__name__}: {e}"
                        )
                        
                        # Wait before retrying
                        time.sleep(delay)
                    else:
                        # Don't retry, re-raise the error
                        raise e
            
            # If we get here, we've exhausted all attempts
            raise last_error
        
        return wrapper
    
    return decorator


def with_circuit_breaker(
    circuit_breaker: CircuitBreaker
):
    """
    Decorator to wrap a function with a circuit breaker.
    
    Args:
        circuit_breaker: The circuit breaker to use
        
    Returns:
        The decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            return circuit_breaker.call(func, *args, **kwargs)
        
        return wrapper
    
    return decorator