"""
Agent Plugin System for AgentMate

This module provides the plugin architecture for agents, allowing
new agent types to be easily added to the system.
"""

from typing import Dict, Type, Optional, Any, List

from Interfaces.agent_interface import IAgent
from Core.plugin_system import plugin_manager, PluginRegistry
from Core.logger import LoggerCreator

logger = LoggerCreator.create_advanced_console("AgentPlugin")


class AgentPlugin:
    """
    Base class for agent plugins.
    
    Agent plugins are responsible for creating and configuring
    agent instances for specific services.
    """
    # The name of the service this agent handles
    service_name: str = None
    
    # The priority of this agent (higher values are higher priority)
    priority: int = 0
    
    # Dependencies on other agents
    dependencies: List[str] = []
    
    @classmethod
    def create_agent(cls, uid: str, service_id: str, **kwargs) -> Optional[IAgent]:
        """
        Create an agent instance.
        
        Args:
            uid: The user ID
            service_id: The service ID
            **kwargs: Additional arguments for agent creation
            
        Returns:
            An agent instance or None if creation fails
        """
        raise NotImplementedError("Agent plugins must implement create_agent")
    
    @classmethod
    def get_config_schema(cls) -> Dict[str, Any]:
        """
        Get the configuration schema for this agent.
        
        Returns:
            A dictionary describing the configuration schema
        """
        return {}
    
    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> bool:
        """
        Validate the configuration for this agent.
        
        Args:
            config: The configuration to validate
            
        Returns:
            True if the configuration is valid, False otherwise
        """
        return True


# Create a registry for agent plugins
agent_registry: PluginRegistry[Type[AgentPlugin]] = plugin_manager.create_registry(
    AgentPlugin, ["Agents"]
)


def register_agent_plugin(service_name: str, plugin_class: Type[AgentPlugin]) -> None:
    """
    Register an agent plugin.
    
    Args:
        service_name: The name of the service this agent handles
        plugin_class: The agent plugin class
    """
    # Set the service name on the plugin class if not already set
    if plugin_class.service_name is None:
        plugin_class.service_name = service_name
    
    agent_registry.register(service_name, plugin_class)
    logger.debug(f"Registered agent plugin for service: {service_name}")


def get_agent_plugin(service_name: str) -> Optional[Type[AgentPlugin]]:
    """
    Get an agent plugin by service name.
    
    Args:
        service_name: The name of the service
        
    Returns:
        The agent plugin class or None if not found
    """
    return agent_registry.get(service_name)


def create_agent(uid: str, service_id: str, service_name: str, **kwargs) -> Optional[IAgent]:
    """
    Create an agent instance using the appropriate plugin.
    
    Args:
        uid: The user ID
        service_id: The service ID
        service_name: The name of the service
        **kwargs: Additional arguments for agent creation
        
    Returns:
        An agent instance or None if no plugin is found
    """
    plugin_class = get_agent_plugin(service_name)
    if plugin_class is None:
        logger.warning(f"No agent plugin found for service: {service_name}")
        return None
    
    try:
        return plugin_class.create_agent(uid, service_id, **kwargs)
    except Exception as e:
        logger.error(f"Failed to create agent for service {service_name}: {str(e)}")
        return None


def discover_agent_plugins() -> None:
    """
    Discover and register all agent plugins.
    """
    agent_registry.discover()
    logger.info(f"Discovered {len(agent_registry.get_all())} agent plugins")


def get_available_agents() -> List[str]:
    """
    Get a list of available agent service names.
    
    Returns:
        A list of service names for which agent plugins are available
    """
    return list(agent_registry.get_all().keys())


def get_agent_dependencies(service_name: str) -> List[str]:
    """
    Get the dependencies for an agent.
    
    Args:
        service_name: The name of the service
        
    Returns:
        A list of service names that this agent depends on
    """
    plugin_class = get_agent_plugin(service_name)
    if plugin_class is None:
        return []
    
    return plugin_class.dependencies