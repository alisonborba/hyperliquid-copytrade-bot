"""
Retry utilities with exponential backoff.
"""

import asyncio
import time
from functools import wraps
from typing import Any, Callable, Optional, Type, Union

import structlog

logger = structlog.get_logger(__name__)


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: Union[Type[Exception], tuple] = Exception,
    on_retry: Optional[Callable[[Exception, int, float], None]] = None,
) -> Callable:
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retries
        base_delay: Base delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        exponential_base: Base for exponential backoff calculation
        exceptions: Exception types to catch and retry
        on_retry: Optional callback function called on each retry
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(
                            "max_retries_exceeded",
                            function=func.__name__,
                            max_retries=max_retries,
                            error=str(e),
                            error_type=type(e).__name__,
                        )
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    
                    logger.warning(
                        "retry_attempt",
                        function=func.__name__,
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        delay=delay,
                        error=str(e),
                        error_type=type(e).__name__,
                    )
                    
                    if on_retry:
                        on_retry(e, attempt + 1, delay)
                    
                    time.sleep(delay)
            
            # This should never be reached, but just in case
            raise last_exception
        
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(
                            "max_retries_exceeded",
                            function=func.__name__,
                            max_retries=max_retries,
                            error=str(e),
                            error_type=type(e).__name__,
                        )
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    
                    logger.warning(
                        "retry_attempt",
                        function=func.__name__,
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        delay=delay,
                        error=str(e),
                        error_type=type(e).__name__,
                    )
                    
                    if on_retry:
                        on_retry(e, attempt + 1, delay)
                    
                    await asyncio.sleep(delay)
            
            # This should never be reached, but just in case
            raise last_exception
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def retry_on_network_error(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
) -> Callable:
    """
    Decorator for retrying functions on network-related errors.
    
    Args:
        max_retries: Maximum number of retries
        base_delay: Base delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        
    Returns:
        Decorated function
    """
    network_exceptions = (
        ConnectionError,
        TimeoutError,
        OSError,
        Exception,  # Catch all for now, can be more specific
    )
    
    def on_retry_callback(exception: Exception, attempt: int, delay: float) -> None:
        """Callback function for network retries."""
        logger.info(
            "network_retry",
            attempt=attempt,
            delay=delay,
            error=str(exception),
            error_type=type(exception).__name__,
        )
    
    return retry_with_backoff(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=max_delay,
        exceptions=network_exceptions,
        on_retry=on_retry_callback,
    )


def retry_on_api_error(
    max_retries: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 10.0,
) -> Callable:
    """
    Decorator for retrying functions on API-related errors.
    
    Args:
        max_retries: Maximum number of retries
        base_delay: Base delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        
    Returns:
        Decorated function
    """
    api_exceptions = (
        Exception,  # Catch all API errors for now
    )
    
    def on_retry_callback(exception: Exception, attempt: int, delay: float) -> None:
        """Callback function for API retries."""
        logger.info(
            "api_retry",
            attempt=attempt,
            delay=delay,
            error=str(exception),
            error_type=type(exception).__name__,
        )
    
    return retry_with_backoff(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=max_delay,
        exceptions=api_exceptions,
        on_retry=on_retry_callback,
    )


class RetryableError(Exception):
    """Base class for retryable errors."""
    pass


class NetworkError(RetryableError):
    """Network-related error."""
    pass


class APIError(RetryableError):
    """API-related error."""
    pass


class RateLimitError(APIError):
    """Rate limit exceeded error."""
    pass


class TemporaryError(RetryableError):
    """Temporary error that should be retried."""
    pass


def is_retryable_error(error: Exception) -> bool:
    """
    Check if an error is retryable.
    
    Args:
        error: Exception to check
        
    Returns:
        True if the error is retryable, False otherwise
    """
    if isinstance(error, RetryableError):
        return True
    
    # Network errors
    if isinstance(error, (ConnectionError, TimeoutError, OSError)):
        return True
    
    # HTTP errors that might be temporary
    if hasattr(error, 'status_code'):
        status_code = getattr(error, 'status_code')
        if status_code in [429, 500, 502, 503, 504]:
            return True
    
    # Timeout errors
    if "timeout" in str(error).lower():
        return True
    
    # Connection errors
    if "connection" in str(error).lower():
        return True
    
    return False


def get_retry_delay(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
) -> float:
    """
    Calculate retry delay with exponential backoff and optional jitter.
    
    Args:
        attempt: Current attempt number (0-based)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential calculation
        jitter: Whether to add jitter to prevent thundering herd
        
    Returns:
        Delay in seconds
    """
    delay = min(base_delay * (exponential_base ** attempt), max_delay)
    
    if jitter:
        # Add up to 25% jitter
        import random
        jitter_factor = 0.25
        jitter_amount = delay * jitter_factor * random.random()
        delay += jitter_amount
    
    return delay
