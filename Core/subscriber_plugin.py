"""
Subscriber Plugin System for AgentMate

This module provides the plugin architecture for subscribers, allowing
new subscriber types to be easily added to the system.
"""

from typing import Dict, Type, Optional, Any, List, Callable, Awaitable

from Subscribers.base_subscriber import BaseSubscriber
from Core.plugin_system import plugin_manager, PluginRegistry
from Core.logger import LoggerCreator

logger = LoggerCreator.create_advanced_console("SubscriberPlugin")


class SubscriberPlugin:
    """
    Base class for subscriber plugins.
    
    Subscriber plugins are responsible for creating and configuring
    subscriber instances for specific event types.
    """
    # The name of this subscriber
    subscriber_name: str = None
    
    # The priority of this subscriber (higher values are higher priority)
    priority: int = 0
    
    # Dependencies on other subscribers
    dependencies: List[str] = []
    
    # Whether this subscriber is enabled by default
    enabled_by_default: bool = True
    
    @classmethod
    def create_subscriber(cls, **kwargs) -> Optional[BaseSubscriber]:
        """
        Create a subscriber instance.
        
        Args:
            **kwargs: Additional arguments for subscriber creation
            
        Returns:
            A subscriber instance or None if creation fails
        """
        raise NotImplementedError("Subscriber plugins must implement create_subscriber")
    
    @classmethod
    def get_config_schema(cls) -> Dict[str, Any]:
        """
        Get the configuration schema for this subscriber.
        
        Returns:
            A dictionary describing the configuration schema
        """
        return {}
    
    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> bool:
        """
        Validate the configuration for this subscriber.
        
        Args:
            config: The configuration to validate
            
        Returns:
            True if the configuration is valid, False otherwise
        """
        return True


# Create a registry for subscriber plugins
subscriber_registry: PluginRegistry[Type[SubscriberPlugin]] = plugin_manager.create_registry(
    SubscriberPlugin, ["Subscribers"]
)


def register_subscriber_plugin(subscriber_name: str, plugin_class: Type[SubscriberPlugin]) -> None:
    """
    Register a subscriber plugin.
    
    Args:
        subscriber_name: The name of this subscriber
        plugin_class: The subscriber plugin class
    """
    # Set the subscriber name on the plugin class if not already set
    if plugin_class.subscriber_name is None:
        plugin_class.subscriber_name = subscriber_name
    
    subscriber_registry.register(subscriber_name, plugin_class)
    logger.debug(f"Registered subscriber plugin: {subscriber_name}")


def get_subscriber_plugin(subscriber_name: str) -> Optional[Type[SubscriberPlugin]]:
    """
    Get a subscriber plugin by name.
    
    Args:
        subscriber_name: The name of the subscriber
        
    Returns:
        The subscriber plugin class or None if not found
    """
    return subscriber_registry.get(subscriber_name)


def create_subscriber(subscriber_name: str, **kwargs) -> Optional[BaseSubscriber]:
    """
    Create a subscriber instance using the appropriate plugin.
    
    Args:
        subscriber_name: The name of the subscriber
        **kwargs: Additional arguments for subscriber creation
        
    Returns:
        A subscriber instance or None if no plugin is found
    """
    plugin_class = get_subscriber_plugin(subscriber_name)
    if plugin_class is None:
        logger.warning(f"No subscriber plugin found for: {subscriber_name}")
        return None
    
    try:
        return plugin_class.create_subscriber(**kwargs)
    except Exception as e:
        logger.error(f"Failed to create subscriber {subscriber_name}: {str(e)}")
        return None


def discover_subscriber_plugins() -> None:
    """
    Discover and register all subscriber plugins.
    """
    subscriber_registry.discover()
    logger.info(f"Discovered {len(subscriber_registry.get_all())} subscriber plugins")


def get_available_subscribers() -> List[str]:
    """
    Get a list of available subscriber names.
    
    Returns:
        A list of subscriber names for which plugins are available
    """
    return list(subscriber_registry.get_all().keys())


def get_subscriber_dependencies(subscriber_name: str) -> List[str]:
    """
    Get the dependencies for a subscriber.
    
    Args:
        subscriber_name: The name of the subscriber
        
    Returns:
        A list of subscriber names that this subscriber depends on
    """
    plugin_class = get_subscriber_plugin(subscriber_name)
    if plugin_class is None:
        return []
    
    return plugin_class.dependencies


def get_subscriber_priority(subscriber_name: str) -> int:
    """
    Get the priority for a subscriber.
    
    Args:
        subscriber_name: The name of the subscriber
        
    Returns:
        The priority of the subscriber (higher values are higher priority)
    """
    plugin_class = get_subscriber_plugin(subscriber_name)
    if plugin_class is None:
        return 0
    
    return plugin_class.priority


def is_subscriber_enabled_by_default(subscriber_name: str) -> bool:
    """
    Check if a subscriber is enabled by default.
    
    Args:
        subscriber_name: The name of the subscriber
        
    Returns:
        True if the subscriber is enabled by default, False otherwise
    """
    plugin_class = get_subscriber_plugin(subscriber_name)
    if plugin_class is None:
        return False
    
    return plugin_class.enabled_by_default