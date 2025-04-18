from typing import Optional, Dict, Any, List, Type


class AgentMateError(Exception):
    """
    Base exception for all AgentMate errors.

    All custom exceptions in the application should inherit from this class.
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize the exception.

        Args:
            message: A human-readable error message
            details: Additional details about the error
        """
        self.message = message
        self.details = details or {}
        super().__init__(message)


# Core Exceptions

class ConfigurationError(AgentMateError):
    """Exception raised for errors in the configuration."""
    pass


class DependencyError(AgentMateError):
    """Exception raised when a required dependency is missing or invalid."""
    pass


class InitializationError(AgentMateError):
    """Exception raised when initialization of a component fails."""
    pass


class ValidationError(AgentMateError):
    """Exception raised when validation of data fails."""
    pass


# Agent Exceptions

class AgentError(AgentMateError):
    """Base exception for all agent-related errors."""

    def __init__(self, message: str, agent_id: Optional[str] = None,
                 service_name: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        """
        Initialize the exception.

        Args:
            message: A human-readable error message
            agent_id: The ID of the agent that caused the error
            service_name: The name of the service associated with the agent
            details: Additional details about the error
        """
        super().__init__(message, details)
        self.agent_id = agent_id
        self.service_name = service_name


class AgentNotFoundError(AgentError):
    """Exception raised when an agent is not found."""
    pass


class AgentInitializationError(AgentError):
    """Exception raised when initialization of an agent fails."""
    pass


class AgentConfigurationError(AgentError):
    """Exception raised when an agent's configuration is invalid."""
    pass


class AgentRuntimeError(AgentError):
    """Exception raised when an agent encounters a runtime error."""
    pass


# Subscriber Exceptions

class SubscriberError(AgentMateError):
    """Base exception for all subscriber-related errors."""

    def __init__(self, message: str, subscriber_name: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        """
        Initialize the exception.

        Args:
            message: A human-readable error message
            subscriber_name: The name of the subscriber that caused the error
            details: Additional details about the error
        """
        super().__init__(message, details)
        self.subscriber_name = subscriber_name


class SubscriberNotFoundError(SubscriberError):
    """Exception raised when a subscriber is not found."""
    pass


class SubscriberInitializationError(SubscriberError):
    """Exception raised when initialization of a subscriber fails."""
    pass


class SubscriberConfigurationError(SubscriberError):
    """Exception raised when a subscriber's configuration is invalid."""
    pass


class SubscriberRuntimeError(SubscriberError):
    """Exception raised when a subscriber encounters a runtime error."""
    pass


# AI Engine Exceptions

class AIEngineError(AgentMateError):
    """Base exception for all AI engine-related errors."""

    def __init__(self, message: str, engine_name: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        """
        Initialize the exception.

        Args:
            message: A human-readable error message
            engine_name: The name of the AI engine that caused the error
            details: Additional details about the error
        """
        super().__init__(message, details)
        self.engine_name = engine_name


class AIRequestError(AIEngineError):
    """Exception raised when an AI request fails."""
    pass


class AIResponseError(AIEngineError):
    """Exception raised when an AI response is invalid or cannot be processed."""
    pass


class AIRateLimitError(AIEngineError):
    """Exception raised when an AI rate limit is exceeded."""
    pass


# Database Exceptions

class DatabaseError(AgentMateError):
    """Base exception for all database-related errors."""
    pass


class DatabaseConnectionError(DatabaseError):
    """Exception raised when a database connection fails."""
    pass


class DatabaseQueryError(DatabaseError):
    """Exception raised when a database query fails."""
    pass


class DatabaseIntegrityError(DatabaseError):
    """Exception raised when a database integrity constraint is violated."""
    pass


# API Exceptions

class APIError(AgentMateError):
    """Base exception for all API-related errors."""

    def __init__(self, message: str, status_code: int = 500,
                 details: Optional[Dict[str, Any]] = None):
        """
        Initialize the exception.

        Args:
            message: A human-readable error message
            status_code: The HTTP status code to return
            details: Additional details about the error
        """
        super().__init__(message, details)
        self.status_code = status_code


class AuthenticationError(APIError):
    """Exception raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed",
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 401, details)


class AuthorizationError(APIError):
    """Exception raised when authorization fails."""

    def __init__(self, message: str = "Not authorized",
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 403, details)


class ResourceNotFoundError(APIError):
    """Exception raised when a requested resource is not found."""

    def __init__(self, message: str = "Resource not found",
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 404, details)


class ValidationAPIError(APIError):
    """Exception raised when validation of API input fails."""

    def __init__(self, message: str = "Validation failed",
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 400, details)


# Utility functions

def get_error_details(error: Exception) -> Dict[str, Any]:
    """
    Get details about an error.

    Args:
        error: The exception to get details for

    Returns:
        A dictionary with error details
    """
    details = {
        "type": error.__class__.__name__,
        "message": str(error),
    }

    if isinstance(error, AgentMateError):
        details.update(error.details)

        if isinstance(error, AgentError):
            if error.agent_id:
                details["agent_id"] = error.agent_id
            if error.service_name:
                details["service_name"] = error.service_name

        elif isinstance(error, SubscriberError):
            if error.subscriber_name:
                details["subscriber_name"] = error.subscriber_name

        elif isinstance(error, AIEngineError):
            if error.engine_name:
                details["engine_name"] = error.engine_name

        elif isinstance(error, APIError):
            details["status_code"] = error.status_code

    return details