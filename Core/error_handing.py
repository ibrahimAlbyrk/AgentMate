import sys
import logging
import traceback
from functools import wraps
from typing import Optional, Dict, Any, Type, TypeVar, Callable, Union, List, Tuple

from Core.exceptions import (
    AgentMateError, get_error_details,
    AIRateLimitError, DatabaseConnectionError
)
from Core.logger import LoggerCreator

# Create a logger for error handling
logger = LoggerCreator.create_advanced_console("ErrorHandler")

T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])


def safe_call_provider(provider: Optional[Callable], *args, **kwargs) -> Any:
    """
    Safely call a provider function with error handling.

    Returns:
        Result of the provider function, or None on error
    """
    try:
        return provider(*args, **kwargs) if provider else None
    except Exception as e:
        logger.warning(f"Error in provider: {e}")
        return None


def handle_error(
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        log_level: int = logging.ERROR,
        reraise: bool = True,
        fallback_value: Optional[Any] = None
) -> Optional[Any]:
    """
    Handle an error in a standardized way.

    Returns:
        The fallback value if reraise is False, otherwise None
    """
    details = get_error_details(error)

    if context:
        details["context"] = context

    exc_type, exc_value, exc_tb = sys.exc_info()
    tb_info = traceback.format_exception(exc_type, exc_value, exc_tb)
    details["traceback"] = tb_info

    error_message = f"{details['type']}: {details['message']}"
    if context:
        context_str = ", ".join(f"{k}={v}" for k, v in context.items())
        error_message = f"{error_message} [{context_str}]"

    logger.log(log_level, error_message, extra={"details": details})

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
    """
    if not error_types:
        error_types = (Exception,)

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except error_types as e:
                context = safe_call_provider(context_provider, *args, **kwargs)
                fallback_value = safe_call_provider(fallback_provider, *args, **kwargs)

                return handle_error(
                    error=e,
                    context=context,
                    log_level=log_level,
                    reraise=reraise,
                    fallback_value=fallback_value
                )

        return wrapper  # type: ignore

    return decorator


def handle_async_errors(
        *error_types: Type[Exception],
        context_provider: Optional[Callable[..., Dict[str, Any]]] = None,
        log_level: int = logging.ERROR,
        reraise: bool = True,
        fallback_provider: Optional[Callable[..., Any]] = None
) -> Callable[[F], F]:
    """
    Decorator to handle errors in a standardized way for async functions.
    """
    if not error_types:
        error_types = (Exception,)

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except error_types as e:
                context = safe_call_provider(context_provider, *args, **kwargs)
                fallback_value = safe_call_provider(fallback_provider, *args, **kwargs)

                return handle_error(
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
    """
    if isinstance(error, (AIRateLimitError, DatabaseConnectionError)):
        return True

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
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except from_type as e:
                message = safe_call_provider(message_provider, e) or str(e)
                details = safe_call_provider(details_provider, e) or {}
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
    """
    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except from_type as e:
                message = safe_call_provider(message_provider, e) or str(e)
                details = safe_call_provider(details_provider, e) or {}
                raise to_type(message, details)

        return wrapper  # type: ignore

    return decorator
