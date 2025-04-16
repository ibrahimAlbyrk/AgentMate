"""
Agent Factory for AgentMate

This module provides a factory for creating agent instances using
the agent plugin system.
"""

from typing import List, Tuple, Optional, Dict, Any

from Interfaces.agent_interface import IAgent
from Core.agent_plugin import (
    create_agent, discover_agent_plugins, get_available_agents,
    get_agent_dependencies, get_agent_plugin
)
from Core.logger import LoggerCreator

logger = LoggerCreator.create_advanced_console("AgentFactory")


class AgentFactory:
    """
    Factory for creating agent instances.

    This class uses the agent plugin system to create agent instances
    for different services.
    """

    @classmethod
    def initialize(cls):
        """
        Initialize the agent factory.

        This method discovers and registers all agent plugins.
        """
        discover_agent_plugins()
        logger.info(f"Available agents: {get_available_agents()}")

    @classmethod
    def create(cls, uid: str, service_id: str, service_name: str, **kwargs) -> Optional[IAgent]:
        """
        Create an agent instance.

        Args:
            uid: The user ID
            service_id: The service ID
            service_name: The name of the service
            **kwargs: Additional arguments for agent creation

        Returns:
            An agent instance or None if creation fails
        """
        return create_agent(uid, service_id, service_name, **kwargs)

    @classmethod
    def create_all(cls, uid: str, services: List[Tuple[str, str]], **kwargs) -> List[IAgent]:
        """
        Create multiple agent instances.

        Args:
            uid: The user ID
            services: A list of (service_id, service_name) tuples
            **kwargs: Additional arguments for agent creation

        Returns:
            A list of agent instances
        """
        agents = []
        for service_id, service_name in services:
            agent = cls.create(uid, service_id, service_name, **kwargs)
            if agent:
                agents.append(agent)
        return agents

    @classmethod
    def get_available_agents(cls) -> List[str]:
        """
        Get a list of available agent service names.

        Returns:
            A list of service names for which agent plugins are available
        """
        return get_available_agents()

    @classmethod
    def get_agent_dependencies(cls, service_name: str) -> List[str]:
        """
        Get the dependencies for an agent.

        Args:
            service_name: The name of the service

        Returns:
            A list of service names that this agent depends on
        """
        return get_agent_dependencies(service_name)

    @classmethod
    def get_agent_config_schema(cls, service_name: str) -> Dict[str, Any]:
        """
        Get the configuration schema for an agent.

        Args:
            service_name: The name of the service

        Returns:
            A dictionary describing the configuration schema
        """
        plugin_class = get_agent_plugin(service_name)
        if plugin_class is None:
            return {}

        return plugin_class.get_config_schema()

    @classmethod
    def validate_agent_config(cls, service_name: str, config: Dict[str, Any]) -> bool:
        """
        Validate the configuration for an agent.

        Args:
            service_name: The name of the service
            config: The configuration to validate

        Returns:
            True if the configuration is valid, False otherwise
        """
        plugin_class = get_agent_plugin(service_name)
        if plugin_class is None:
            return False

        return plugin_class.validate_config(config)
