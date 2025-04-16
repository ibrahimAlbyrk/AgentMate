"""
Error Handling Utilities for AgentMate

This module provides utilities for handling and logging errors in a standardized way
throughout the application.
"""

import sys
import traceback
import logging
from typing import Optional, Dict, Any, Type, TypeVar, Callable, Union, List, Tuple
from functools import wraps

from Core.exceptions import (
    AgentMateError, get_error_details,
    AIRateLimitError, DatabaseConnectionError
)
from Core.logger import LoggerCreator

# Create a logger for error handling
logger = LoggerCreator.create_advanced_console("ErrorHandler")

T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])


def handle_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    log_level: int = logging.ERROR,
    reraise: bool = True,
    fallback_value: Optional[Any] = None
) -> Optional[Any]:
    """
    Handle an error in a standardized way.
    
    Args:
        error: The exception to handle
        context: Additional context information
        log_level: The logging level to use
        reraise: Whether to reraise the exception
        fallback_value: Value to return if not reraising
        
    Returns:
        The fallback value if reraise is False, otherwise None
        
    Raises:
        The original exception if reraise is True
    """
    # Get error details
    details = get_error_details(error)
    
    # Add context if provided
    if context:
        details["context"] = context
    
    # Get traceback information
    tb_info = traceback.format_exception(*sys.exc_info())
    details["traceback"] = tb_info
    
    # Log the error
    error_message = f"{details['type']}: {details['message']}"
    if context:
        context_str = ", ".join(f"{k}={v}" for k, v in context.items())
        error_message = f"{error_message} [{context_str}]"
    
    if log_level == logging.DEBUG:
        logger.debug(error_message, extra={"details": details})
    elif log_level == logging.INFO:
        logger.info(error_message, extra={"details": details})
    elif log_level == logging.WARNING:
        logger.warning(error_message, extra={"details": details})
    elif log_level == logging.ERROR:
        logger.error(error_message, extra={"details": details})
    elif log_level == logging.CRITICAL:
        logger.critical(error_message, extra={"details": details})
    
    # Reraise or return fallback
    if reraise:
        raise error
    
    return fallback_value


def handle_errors(
    *error_types: Type[Exception],
    context_provider: Optional[Callable[..., Dict[str, Any]]] = None,
    log_level: int = logging.ERROR,
    reraise: bool = True,
    fallback_provider: Optional[Callable[..., Any]] = None
) -> Callable[[F], F]:
    """
    Decorator to handle errors in a standardized way.
    
    Args:
        *error_types: The types of exceptions to catch
        context_provider: Function to provide context information
        log_level: The logging level to use
        reraise: Whether to reraise the exception
        fallback_provider: Function to provide a fallback value
        
    Returns:
        A decorator function
    """
    if not error_types:
        error_types = (Exception,)
    
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except error_types as e:
                # Get context if provider is specified
                context = None
                if context_provider:
                    try:
                        context = context_provider(*args, **kwargs)
                    except Exception as context_error:
                        logger.warning(f"Error getting context: {str(context_error)}")
                
                # Get fallback value if provider is specified
                fallback_value = None
                if fallback_provider:
                    try:
                        fallback_value = fallback_provider(*args, **kwargs)
                    except Exception as fallback_error:
                        logger.warning(f"Error getting fallback value: {str(fallback_error)}")
                
                # Handle the error
                return handle_error(
                    error=e,
                    context=context,
                    log_level=log_level,
                    reraise=reraise,
                    fallback_value=fallback_value
                )
        
        return wrapper  # type: ignore
    
    return decorator


async def handle_async_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    log_level: int = logging.ERROR,
    reraise: bool = True,
    fallback_value: Optional[Any] = None
) -> Optional[Any]:
    """
    Handle an error in a standardized way for async functions.
    
    Args:
        error: The exception to handle
        context: Additional context information
        log_level: The logging level to use
        reraise: Whether to reraise the exception
        fallback_value: Value to return if not reraising
        
    Returns:
        The fallback value if reraise is False, otherwise None
        
    Raises:
        The original exception if reraise is True
    """
    # Use the synchronous handler
    return handle_error(
        error=error,
        context=context,
        log_level=log_level,
        reraise=reraise,
        fallback_value=fallback_value
    )


def handle_async_errors(
    *error_types: Type[Exception],
    context_provider: Optional[Callable[..., Dict[str, Any]]] = None,
    log_level: int = logging.ERROR,
    reraise: bool = True,
    fallback_provider: Optional[Callable[..., Any]] = None
) -> Callable[[F], F]:
    """
    Decorator to handle errors in a standardized way for async functions.
    
    Args:
        *error_types: The types of exceptions to catch
        context_provider: Function to provide context information
        log_level: The logging level to use
        reraise: Whether to reraise the exception
        fallback_provider: Function to provide a fallback value
        
    Returns:
        A decorator function
    """
    if not error_types:
        error_types = (Exception,)
    
    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except error_types as e:
                # Get context if provider is specified
                context = None
                if context_provider:
                    try:
                        context = context_provider(*args, **kwargs)
                    except Exception as context_error:
                        logger.warning(f"Error getting context: {str(context_error)}")
                
                # Get fallback value if provider is specified
                fallback_value = None
                if fallback_provider:
                    try:
                        fallback_value = fallback_provider(*args, **kwargs)
                    except Exception as fallback_error:
                        logger.warning(f"Error getting fallback value: {str(fallback_error)}")
                
                # Handle the error
                return await handle_async_error(
                    error=e,
                    context=context,
                    log_level=log_level,
                    reraise=reraise,
                    fallback_value=fallback_value
                )
        
        return wrapper  # type: ignore
    
    return decorator


def should_retry_error(error: Exception) -> bool:
    """
    Determine if an error should be retried.
    
    Args:
        error: The exception to check
        
    Returns:
        True if the error should be retried, False otherwise
    """
    # Retry rate limit errors
    if isinstance(error, AIRateLimitError):
        return True
    
    # Retry database connection errors
    if isinstance(error, DatabaseConnectionError):
        return True
    
    # Check for "retry" in error details
    if isinstance(error, AgentMateError) and error.details.get("retry", False):
        return True
    
    return False


def convert_exception(
    from_type: Type[Exception],
    to_type: Type[Exception],
    message_provider: Optional[Callable[[Exception], str]] = None,
    details_provider: Optional[Callable[[Exception], Dict[str, Any]]] = None
) -> Callable[[F], F]:
    """
    Decorator to convert one exception type to another.
    
    Args:
        from_type: The type of exception to convert from
        to_type: The type of exception to convert to
        message_provider: Function to provide the new error message
        details_provider: Function to provide the new error details
        
    Returns:
        A decorator function
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except from_type as e:
                # Get message if provider is specified
                message = str(e)
                if message_provider:
                    try:
                        message = message_provider(e)
                    except Exception:
                        pass
                
                # Get details if provider is specified
                details = {}
                if details_provider:
                    try:
                        details = details_provider(e)
                    except Exception:
                        pass
                
                # Convert the exception
                raise to_type(message, details)
        
        return wrapper  # type: ignore
    
    return decorator


def convert_async_exception(
    from_type: Type[Exception],
    to_type: Type[Exception],
    message_provider: Optional[Callable[[Exception], str]] = None,
    details_provider: Optional[Callable[[Exception], Dict[str, Any]]] = None
) -> Callable[[F], F]:
    """
    Decorator to convert one exception type to another for async functions.
    
    Args:
        from_type: The type of exception to convert from
        to_type: The type of exception to convert to
        message_provider: Function to provide the new error message
        details_provider: Function to provide the new error details
        
    Returns:
        A decorator function
    """
    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except from_type as e:
                # Get message if provider is specified
                message = str(e)
                if message_provider:
                    try:
                        message = message_provider(e)
                    except Exception:
                        pass
                
                # Get details if provider is specified
                details = {}
                if details_provider:
                    try:
                        details = details_provider(e)
                    except Exception:
                        pass
                
                # Convert the exception
                raise to_type(message, details)
        
        return wrapper  # type: ignore
    
    return decorator