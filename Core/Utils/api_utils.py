import json
import logging
from typing import Dict, Any, TypeVar, Callable, Optional, Generator, Union, List, Type

from Core.logger import LoggerCreator
from Core.error_handling import handle_error, handle_async_error

T = TypeVar("T")
R = TypeVar("R")


class APIResponseHandler:
    """
    Utility for handling API responses.

    This class provides methods for safely processing API responses
    and handling errors in a standardized way.
    """

    def __init__(self, logger_name: str = "APIResponseHandler"):
        self.logger = LoggerCreator.create_advanced_console(logger_name)

    def process_response(self,
                         response: Dict[str, Any],
                         processor: Callable[[Dict[str, Any]], T],
                         error_message: str = "Error processing API response",
                         default_value: Optional[T] = None,
                         log_level: int = logging.ERROR) -> T:
        """
        Process an API response safely.

        Args:
            response: The API response to process
            processor: A function to process the response
            error_message: The error message to log if processing fails
            default_value: The default value to return if processing fails
            log_level: The logging level to use for errors

        Returns:
            The processed response or the default value if processing fails
        """
        try:
            return processor(response)
        except Exception as e:
            context = {'response': str(response[:200] + "..." if len(str(response)) > 200 else str(response))}
            return handle_error(
                error=f"{error_message}: {e}",
                context=context,
                log_level=log_level,
                reraise=False,
                fallback_value=default_value or {},
            )

    async def process_async_response(self,
                                     response: Dict[str, Any],
                                     processor: Callable[[Dict[str, Any]], T],
                                     error_message: str = "Error processing API response",
                                     default_value: Optional[T] = None,
                                     log_level: int = logging.ERROR) -> T:
        """
        Process an API response safely (async version).

        Args:
            response: The API response to process
            processor: A function to process the response
            error_message: The error message to log if processing fails
            default_value: The default value to return if processing fails
            log_level: The logging level to use for errors

        Returns:
            The processed response or the default value if processing fails
        """
        try:
            return processor(response)
        except Exception as e:
            context = {"response": str(response)[:200] + "..." if len(str(response)) > 200 else str(response)}
            return await handle_async_error(
                error=f"{error_message}: {e}",
                context=context,
                log_level=log_level,
                reraise=False,
                fallback_value=default_value or {}
            )

    def parse_json(self,
                   json_str: str,
                   error_message: str = "Error parsing JSON",
                   default_value: Optional[Dict[str, Any]] = None,
                   log_level: int = logging.ERROR) -> Dict[str, Any]:
        """
        Parse a JSON string safely.

        Args:
            json_str: The JSON string to parse
            error_message: The error message to log if parsing fails
            default_value: The default value to return if parsing fails
            log_level: The logging level to use for errors

        Returns:
            The parsed JSON or the default value if parsing fails
        """
        try:
            return json.loads(json_str)
        except Exception as e:
            context = {"json_str": json_str[:200] + "..." if len(json_str) > 200 else json_str}
            return handle_error(
                error=f"{error_message}: {e}",
                context=context,
                log_level=log_level,
                reraise=False,
                fallback_value=default_value or {}
            )

    def serialize_json(self,
                       data: Dict[str, Any],
                       error_message: str = "Error serializing JSON",
                       default_value: str = "{}",
                       log_level: int = logging.ERROR) -> str:
        """
        Serialize data to a JSON string safely.

        Args:
            data: The data to serialize
            error_message: The error message to log if serialization fails
            default_value: The default value to return if serialization fails
            log_level: The logging level to use for errors

        Returns:
            The serialized JSON or the default value if serialization fails
        """
        try:
            return json.dumps(data)
        except Exception as e:
            context = {"data": str(data)[:200] + "..." if len(str(data)) > 200 else str(data)}
            return handle_error(
                error=f"{error_message}: {e}",
                context=context,
                log_level=log_level,
                reraise=False,
                fallback_value=default_value
            )


api_utils = APIResponseHandler()
