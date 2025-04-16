"""
Agent Interface for AgentMate

This module defines the interface for agents in the AgentMate system.
Agents are components that perform tasks for users, such as processing
emails or managing calendar events.
"""

from abc import ABC, abstractmethod
from typing import Optional, Coroutine, Any, Dict, List, ClassVar, Type
from enum import Enum
from datetime import datetime

from composio_openai import ComposioToolSet, App, Action

from Core.config import settings
from Core.logger import LoggerCreator
from Core.Models.domain import AgentStatus, AgentHealth

from Agents.LLM.llm_agent import LLMAgent, LLMActionData

from DB.Services.user_settings_service import UserSettingsService

toolset = ComposioToolSet(api_key=settings.api.composio_api_key)


class AgentVersion:
    """
    Represents the version of an agent.

    This class is used to track agent versions for backward compatibility.
    """
    MAJOR: int = 1
    MINOR: int = 0
    PATCH: int = 0

    @classmethod
    def as_string(cls) -> str:
        """Get the version as a string."""
        return f"{cls.MAJOR}.{cls.MINOR}.{cls.PATCH}"

    @classmethod
    def is_compatible_with(cls, other: 'AgentVersion') -> bool:
        """Check if this version is compatible with another version."""
        return cls.MAJOR == other.MAJOR


class AgentLifecycleState(str, Enum):
    """
    Represents the lifecycle state of an agent.
    """
    CREATED = "created"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class IAgent(ABC):
    """
    Interface for agents in the AgentMate system.

    Agents are components that perform tasks for users, such as
    processing emails or managing calendar events.
    """
    # Class-level attributes
    VERSION: ClassVar[AgentVersion] = AgentVersion()
    DEPENDENCIES: ClassVar[List[str]] = []
    CONFIG_SCHEMA: ClassVar[Dict[str, Any]] = {}

    def __init__(self, uid: str, service_id: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the agent.

        Args:
            uid: The user ID
            service_id: The service ID
            config: Configuration for the agent
        """
        self.uid = uid
        self.service_id = service_id
        self.config = config or {}

        # Agent state
        self.lifecycle_state = AgentLifecycleState.CREATED
        self.status = AgentStatus.IDLE
        self.health = AgentHealth.UNKNOWN
        self.last_active = datetime.now()
        self.error = None

        # LLM components
        self.actions: Dict[str, LLMActionData] = {}
        self.llm: Optional[LLMAgent] = None

        # Composio components
        self.entity = toolset.get_entity(uid)
        self.app_name: Optional[App] = None
        self.listener = toolset.create_trigger_listener()
        self._listener_refs = []

        # Logging
        self.logger = LoggerCreator.create_advanced_console(self.__class__.__name__)

    def initialize_llm(self, actions: Dict[str, LLMActionData] = None):
        """
        Initialize the LLM component of the agent.

        Args:
            actions: LLM actions for the agent
        """
        self.actions = actions or {}
        self.llm = LLMAgent(self.app_name, self.uid, self.service_id, self.actions)

    def add_listener(self, trigger_name: str, handler: callable, config: Optional[Dict[str, Any]] = None):
        """
        Add a listener for a trigger.

        Args:
            trigger_name: The name of the trigger
            handler: The handler function
            config: Configuration for the trigger
        """
        config = config or {}

        self.entity.enable_trigger(
            app=self.app_name,
            trigger_name=trigger_name,
            config=config
        )

        decorated = self.listener.callback(filters={"trigger_name": trigger_name})(handler)
        self._listener_refs.append(decorated)

    async def initialize(self) -> bool:
        """
        Initialize the agent.

        This method should be called before running the agent.
        It performs any necessary setup and validation.

        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            self.lifecycle_state = AgentLifecycleState.INITIALIZING

            # Validate configuration
            if not self._validate_config():
                self.logger.error(f"Invalid configuration for agent {self.__class__.__name__}")
                self.lifecycle_state = AgentLifecycleState.ERROR
                self.error = "Invalid configuration"
                return False

            # Initialize agent-specific components
            success = await self._initialize_impl()

            if success:
                self.lifecycle_state = AgentLifecycleState.STOPPED
                self.health = AgentHealth.HEALTHY
                return True
            else:
                self.lifecycle_state = AgentLifecycleState.ERROR
                self.health = AgentHealth.UNHEALTHY
                return False

        except Exception as e:
            self.logger.error(f"Error initializing agent: {str(e)}")
            self.lifecycle_state = AgentLifecycleState.ERROR
            self.health = AgentHealth.UNHEALTHY
            self.error = str(e)
            return False

    async def run(self) -> bool:
        """
        Run the agent.

        This method starts the agent's main processing loop.

        Returns:
            True if the agent was started successfully, False otherwise
        """
        try:
            if self.lifecycle_state not in [AgentLifecycleState.STOPPED, AgentLifecycleState.PAUSED]:
                if self.lifecycle_state == AgentLifecycleState.CREATED:
                    # Initialize if not already initialized
                    success = await self.initialize()
                    if not success:
                        return False
                else:
                    self.logger.warning(f"Cannot run agent in state: {self.lifecycle_state}")
                    return False

            self.lifecycle_state = AgentLifecycleState.RUNNING
            self.status = AgentStatus.RUNNING
            self.last_active = datetime.now()

            # Run agent-specific implementation
            success = await self._run_impl()

            if not success:
                self.lifecycle_state = AgentLifecycleState.ERROR
                self.status = AgentStatus.ERROR
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error running agent: {str(e)}")
            self.lifecycle_state = AgentLifecycleState.ERROR
            self.status = AgentStatus.ERROR
            self.error = str(e)
            return False

    async def pause(self) -> bool:
        """
        Pause the agent.

        This method temporarily suspends the agent's processing.

        Returns:
            True if the agent was paused successfully, False otherwise
        """
        try:
            if self.lifecycle_state != AgentLifecycleState.RUNNING:
                self.logger.warning(f"Cannot pause agent in state: {self.lifecycle_state}")
                return False

            self.lifecycle_state = AgentLifecycleState.PAUSED

            # Pause agent-specific implementation
            success = await self._pause_impl()

            if not success:
                self.lifecycle_state = AgentLifecycleState.ERROR
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error pausing agent: {str(e)}")
            self.lifecycle_state = AgentLifecycleState.ERROR
            self.error = str(e)
            return False

    async def resume(self) -> bool:
        """
        Resume the agent.

        This method resumes a paused agent.

        Returns:
            True if the agent was resumed successfully, False otherwise
        """
        try:
            if self.lifecycle_state != AgentLifecycleState.PAUSED:
                self.logger.warning(f"Cannot resume agent in state: {self.lifecycle_state}")
                return False

            self.lifecycle_state = AgentLifecycleState.RUNNING

            # Resume agent-specific implementation
            success = await self._resume_impl()

            if not success:
                self.lifecycle_state = AgentLifecycleState.ERROR
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error resuming agent: {str(e)}")
            self.lifecycle_state = AgentLifecycleState.ERROR
            self.error = str(e)
            return False

    async def stop(self) -> bool:
        """
        Stop the agent.

        This method stops the agent's processing and performs cleanup.

        Returns:
            True if the agent was stopped successfully, False otherwise
        """
        try:
            if self.lifecycle_state not in [AgentLifecycleState.RUNNING, AgentLifecycleState.PAUSED]:
                self.logger.warning(f"Cannot stop agent in state: {self.lifecycle_state}")
                return False

            self.lifecycle_state = AgentLifecycleState.STOPPING

            # Clean up listeners
            self.listener.stop()
            del self._listener_refs

            # Stop agent-specific implementation
            success = await self._stop_impl()

            if success:
                self.lifecycle_state = AgentLifecycleState.STOPPED
                self.status = AgentStatus.STOPPED
                return True
            else:
                self.lifecycle_state = AgentLifecycleState.ERROR
                self.status = AgentStatus.ERROR
                return False

        except Exception as e:
            self.logger.error(f"Error stopping agent: {str(e)}")
            self.lifecycle_state = AgentLifecycleState.ERROR
            self.status = AgentStatus.ERROR
            self.error = str(e)
            return False

    async def check_health(self) -> AgentHealth:
        """
        Check the health of the agent.

        This method performs a health check on the agent and updates
        the health status.

        Returns:
            The current health status of the agent
        """
        try:
            # Check agent-specific health
            health = await self._check_health_impl()
            self.health = health
            return health

        except Exception as e:
            self.logger.error(f"Error checking agent health: {str(e)}")
            self.health = AgentHealth.UNHEALTHY
            return AgentHealth.UNHEALTHY

    def _validate_config(self) -> bool:
        """
        Validate the agent configuration.

        Returns:
            True if the configuration is valid, False otherwise
        """
        # Basic validation against schema
        for key, schema in self.CONFIG_SCHEMA.items():
            if key not in self.config and schema.get('required', False):
                self.logger.error(f"Missing required configuration key: {key}")
                return False

        # Agent-specific validation
        return self._validate_config_impl()

    def _validate_config_impl(self) -> bool:
        """
        Validate the agent configuration (implementation).

        This method should be overridden by agent implementations
        to perform agent-specific configuration validation.

        Returns:
            True if the configuration is valid, False otherwise
        """
        return True

    @abstractmethod
    async def _initialize_impl(self) -> bool:
        """
        Initialize the agent (implementation).

        This method should be overridden by agent implementations
        to perform agent-specific initialization.

        Returns:
            True if initialization was successful, False otherwise
        """
        pass

    @abstractmethod
    async def _run_impl(self) -> bool:
        """
        Run the agent (implementation).

        This method should be overridden by agent implementations
        to perform agent-specific processing.

        Returns:
            True if the agent was started successfully, False otherwise
        """
        pass

    async def _pause_impl(self) -> bool:
        """
        Pause the agent (implementation).

        This method should be overridden by agent implementations
        to perform agent-specific pausing.

        Returns:
            True if the agent was paused successfully, False otherwise
        """
        return True

    async def _resume_impl(self) -> bool:
        """
        Resume the agent (implementation).

        This method should be overridden by agent implementations
        to perform agent-specific resuming.

        Returns:
            True if the agent was resumed successfully, False otherwise
        """
        return True

    @abstractmethod
    async def _stop_impl(self) -> bool:
        """
        Stop the agent (implementation).

        This method should be overridden by agent implementations
        to perform agent-specific cleanup.

        Returns:
            True if the agent was stopped successfully, False otherwise
        """
        pass

    async def _check_health_impl(self) -> AgentHealth:
        """
        Check the health of the agent (implementation).

        This method should be overridden by agent implementations
        to perform agent-specific health checks.

        Returns:
            The current health status of the agent
        """
        return AgentHealth.HEALTHY
