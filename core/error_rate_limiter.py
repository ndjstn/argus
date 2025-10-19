"""
Error rate limiter for the agentic system.
"""

import time
import logging
from typing import Dict, Optional
from collections import defaultdict, deque
from threading import Lock


class ErrorRateLimiter:
    """Rate limiter for error logging to prevent log flooding."""
    
    def __init__(
        self,
        max_errors_per_second: int = 10,
        max_errors_per_minute: int = 100,
        window_size_seconds: int = 60
    ):
        """
        Initialize the error rate limiter.
        
        Args:
            max_errors_per_second: Maximum number of errors allowed per second
            max_errors_per_minute: Maximum number of errors allowed per minute
            window_size_seconds: Size of the sliding window in seconds
        """
        self.max_errors_per_second = max_errors_per_second
        self.max_errors_per_minute = max_errors_per_minute
        self.window_size_seconds = window_size_seconds
        
        # Sliding window for error tracking
        self.error_timestamps = deque()
        self.error_counts_per_second = defaultdict(int)
        self.error_counts_per_minute = defaultdict(int)
        
        # Lock for thread safety
        self.lock = Lock()
        
        self.logger = logging.getLogger("error_rate_limiter")
    
    def is_allowed(self, error_type: str) -> bool:
        """
        Check if logging an error of the given type is allowed.
        
        Args:
            error_type: The type of error
            
        Returns:
            True if logging is allowed, False otherwise
        """
        with self.lock:
            current_time = time.time()
            current_second = int(current_time)
            current_minute = int(current_time // 60)
            
            # Remove old timestamps outside the window
            while self.error_timestamps and current_time - self.error_timestamps[0] > self.window_size_seconds:
                old_timestamp = self.error_timestamps.popleft()
                old_second = int(old_timestamp)
                old_minute = int(old_timestamp // 60)
                
                # Decrement counts for old timestamps
                self.error_counts_per_second[old_second] -= 1
                if self.error_counts_per_second[old_second] <= 0:
                    del self.error_counts_per_second[old_second]
                
                self.error_counts_per_minute[old_minute] -= 1
                if self.error_counts_per_minute[old_minute] <= 0:
                    del self.error_counts_per_minute[old_minute]
            
            # Check rate limits
            if self.error_counts_per_second.get(current_second, 0) >= self.max_errors_per_second:
                self.logger.debug(f"Rate limit exceeded for errors per second: {error_type}")
                return False
            
            if self.error_counts_per_minute.get(current_minute, 0) >= self.max_errors_per_minute:
                self.logger.debug(f"Rate limit exceeded for errors per minute: {error_type}")
                return False
            
            # Update counts
            self.error_timestamps.append(current_time)
            self.error_counts_per_second[current_second] += 1
            self.error_counts_per_minute[current_minute] += 1
            
            return True
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get rate limiter statistics.
        
        Returns:
            Dictionary with statistics
        """
        with self.lock:
            current_time = time.time()
            current_second = int(current_time)
            current_minute = int(current_time // 60)
            
            return {
                "errors_in_current_second": self.error_counts_per_second.get(current_second, 0),
                "errors_in_current_minute": self.error_counts_per_minute.get(current_minute, 0),
                "max_errors_per_second": self.max_errors_per_second,
                "max_errors_per_minute": self.max_errors_per_minute,
                "window_size_seconds": self.window_size_seconds
            }


class AdaptiveErrorRateLimiter:
    """Adaptive error rate limiter that adjusts limits based on error patterns."""
    
    def __init__(
        self,
        initial_max_errors_per_second: int = 10,
        initial_max_errors_per_minute: int = 100,
        max_errors_per_second: int = None,
        max_errors_per_minute: int = None,
        window_size_seconds: int = 60,
        adjustment_threshold: float = 0.8,
        adjustment_factor: float = 1.5
    ):
        """
        Initialize the adaptive error rate limiter.
        
        Args:
            initial_max_errors_per_second: Initial maximum number of errors allowed per second
            initial_max_errors_per_minute: Initial maximum number of errors allowed per minute
            max_errors_per_second: Current maximum number of errors allowed per second (for compatibility)
            max_errors_per_minute: Current maximum number of errors allowed per minute (for compatibility)
            window_size_seconds: Size of the sliding window in seconds
            adjustment_threshold: Threshold for adjusting limits (0.0 to 1.0)
            adjustment_factor: Factor to adjust limits by
        """
        self.initial_max_errors_per_second = initial_max_errors_per_second
        self.initial_max_errors_per_minute = initial_max_errors_per_minute
        self.window_size_seconds = window_size_seconds
        self.adjustment_threshold = adjustment_threshold
        self.adjustment_factor = adjustment_factor
        
        # Current limits
        self.max_errors_per_second = max_errors_per_second or initial_max_errors_per_second
        self.max_errors_per_minute = max_errors_per_minute or initial_max_errors_per_minute
        
        # Sliding window for error tracking
        self.error_timestamps = deque()
        self.error_counts_per_second = defaultdict(int)
        self.error_counts_per_minute = defaultdict(int)
        
        # Error type tracking
        self.error_type_counts = defaultdict(int)
        
        # Lock for thread safety
        self.lock = Lock()
        
        self.logger = logging.getLogger("adaptive_error_rate_limiter")
    
    def is_allowed(self, error_type: str) -> bool:
        """
        Check if logging an error of the given type is allowed.
        
        Args:
            error_type: The type of error
            
        Returns:
            True if logging is allowed, False otherwise
        """
        with self.lock:
            current_time = time.time()
            current_second = int(current_time)
            current_minute = int(current_time // 60)
            
            # Remove old timestamps outside the window
            while self.error_timestamps and current_time - self.error_timestamps[0] > self.window_size_seconds:
                old_timestamp = self.error_timestamps.popleft()
                old_second = int(old_timestamp)
                old_minute = int(old_timestamp // 60)
                
                # Decrement counts for old timestamps
                self.error_counts_per_second[old_second] -= 1
                if self.error_counts_per_second[old_second] <= 0:
                    del self.error_counts_per_second[old_second]
                
                self.error_counts_per_minute[old_minute] -= 1
                if self.error_counts_per_minute[old_minute] <= 0:
                    del self.error_counts_per_minute[old_minute]
            
            # Check rate limits
            if self.error_counts_per_second.get(current_second, 0) >= self.max_errors_per_second:
                self.logger.debug(f"Rate limit exceeded for errors per second: {error_type}")
                return False
            
            if self.error_counts_per_minute.get(current_minute, 0) >= self.max_errors_per_minute:
                self.logger.debug(f"Rate limit exceeded for errors per minute: {error_type}")
                return False
            
            # Update counts
            self.error_timestamps.append(current_time)
            self.error_counts_per_second[current_second] += 1
            self.error_counts_per_minute[current_minute] += 1
            self.error_type_counts[error_type] += 1
            
            # Check if we need to adjust limits
            self._adjust_limits()
            
            return True
    
    def _adjust_limits(self):
        """Adjust rate limits based on error patterns."""
        # Only adjust if we have enough data
        if len(self.error_timestamps) < 10:
            return
        
        # Calculate current usage percentages
        current_time = time.time()
        current_second = int(current_time)
        current_minute = int(current_time // 60)
        
        second_usage = self.error_counts_per_second.get(current_second, 0) / self.max_errors_per_second
        minute_usage = self.error_counts_per_minute.get(current_minute, 0) / self.max_errors_per_minute
        
        # Adjust limits if usage is consistently high
        if second_usage > self.adjustment_threshold and minute_usage > self.adjustment_threshold:
            # Increase limits
            self.max_errors_per_second = int(self.max_errors_per_second * self.adjustment_factor)
            self.max_errors_per_minute = int(self.max_errors_per_minute * self.adjustment_factor)
            self.logger.info(
                f"Adjusted rate limits upward: {self.max_errors_per_second}/sec, "
                f"{self.max_errors_per_minute}/min"
            )
        elif second_usage < 0.1 and minute_usage < 0.1:
            # Decrease limits if usage is consistently low, but not below initial values
            new_second_limit = max(
                self.initial_max_errors_per_second,
                int(self.max_errors_per_second / self.adjustment_factor)
            )
            new_minute_limit = max(
                self.initial_max_errors_per_minute,
                int(self.max_errors_per_minute / self.adjustment_factor)
            )
            
            if new_second_limit != self.max_errors_per_second or new_minute_limit != self.max_errors_per_minute:
                self.max_errors_per_second = new_second_limit
                self.max_errors_per_minute = new_minute_limit
                self.logger.info(
                    f"Adjusted rate limits downward: {self.max_errors_per_second}/sec, "
                    f"{self.max_errors_per_minute}/min"
                )
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get rate limiter statistics.
        
        Returns:
            Dictionary with statistics
        """
        with self.lock:
            current_time = time.time()
            current_second = int(current_time)
            current_minute = int(current_time // 60)
            
            return {
                "errors_in_current_second": self.error_counts_per_second.get(current_second, 0),
                "errors_in_current_minute": self.error_counts_per_minute.get(current_minute, 0),
                "max_errors_per_second": self.max_errors_per_second,
                "max_errors_per_minute": self.max_errors_per_minute,
                "window_size_seconds": self.window_size_seconds
            }
    
    def get_error_type_stats(self) -> Dict[str, int]:
        """
        Get error type statistics.
        
        Returns:
            Dictionary with error type counts
        """
        with self.lock:
            return dict(self.error_type_counts)


# Global instances
_rate_limiter: Optional[ErrorRateLimiter] = None
_adaptive_rate_limiter: Optional[AdaptiveErrorRateLimiter] = None


def initialize_rate_limiter(
    max_errors_per_second: int = 10,
    max_errors_per_minute: int = 100,
    window_size_seconds: int = 60
):
    """
    Initialize the global error rate limiter.
    
    Args:
        max_errors_per_second: Maximum number of errors allowed per second
        max_errors_per_minute: Maximum number of errors allowed per minute
        window_size_seconds: Size of the sliding window in seconds
    """
    global _rate_limiter
    _rate_limiter = ErrorRateLimiter(
        max_errors_per_second=max_errors_per_second,
        max_errors_per_minute=max_errors_per_minute,
        window_size_seconds=window_size_seconds
    )


def initialize_adaptive_rate_limiter(
    initial_max_errors_per_second: int = 10,
    initial_max_errors_per_minute: int = 100,
    window_size_seconds: int = 60,
    adjustment_threshold: float = 0.8,
    adjustment_factor: float = 1.5
):
    """
    Initialize the global adaptive error rate limiter.
    
    Args:
        initial_max_errors_per_second: Initial maximum number of errors allowed per second
        initial_max_errors_per_minute: Initial maximum number of errors allowed per minute
        window_size_seconds: Size of the sliding window in seconds
        adjustment_threshold: Threshold for adjusting limits (0.0 to 1.0)
        adjustment_factor: Factor to adjust limits by
    """
    global _adaptive_rate_limiter
    _adaptive_rate_limiter = AdaptiveErrorRateLimiter(
        initial_max_errors_per_second=initial_max_errors_per_second,
        initial_max_errors_per_minute=initial_max_errors_per_minute,
        window_size_seconds=window_size_seconds,
        adjustment_threshold=adjustment_threshold,
        adjustment_factor=adjustment_factor
    )


def get_rate_limiter() -> Optional[ErrorRateLimiter]:
    """
    Get the global error rate limiter instance.
    
    Returns:
        The error rate limiter instance, or None if not initialized
    """
    global _rate_limiter
    return _rate_limiter


def get_adaptive_rate_limiter() -> Optional[AdaptiveErrorRateLimiter]:
    """
    Get the global adaptive error rate limiter instance.
    
    Returns:
        The adaptive error rate limiter instance, or None if not initialized
    """
    global _adaptive_rate_limiter
    return _adaptive_rate_limiter


def is_error_logging_allowed(error_type: str, use_adaptive: bool = False) -> bool:
    """
    Check if logging an error is allowed based on rate limits.
    
    Args:
        error_type: The type of error
        use_adaptive: Whether to use the adaptive rate limiter
        
    Returns:
        True if logging is allowed, False otherwise
    """
    if use_adaptive:
        limiter = get_adaptive_rate_limiter()
    else:
        limiter = get_rate_limiter()
    
    if not limiter:
        # If no limiter is configured, allow all errors
        return True
    
    return limiter.is_allowed(error_type)