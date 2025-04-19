from typing import Dict, Type, Optional, Any, List, Callable, Awaitable

from Core.logger import LoggerCreator
from Core.plugin_system import plugin_manager, PluginRegistry

from Subscribers.base_subscriber import BaseSubscriber

logger = LoggerCreator.create_advanced_console("SubscriberPlugin")


class SubscriberPlugin:
    """
    Base class for subscriber plugins.

    Subscriber plugins are responsible for creating and configuring
    subscriber instances for specific event types.
    """
    subscriber_name: str = None

    # The priority of this subscriber (higher values are higher priority)
    priority: int = 0

    dependencies: List[str] = []

    enabled_by_default: bool = True

    @classmethod
    def create_subscriber(cls, **kwargs) -> Optional[BaseSubscriber]:
        """
        Args:
            **kwargs: Additional arguments for subscriber creation
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


subscriber_registry: PluginRegistry[Type[SubscriberPlugin]] = plugin_manager.create_registry(
    SubscriberPlugin, ["Subscribers"]
)


def register_subscriber_plugin(subscriber_name: str, plugin_class: Type[SubscriberPlugin]) -> None:
    if plugin_class.subscriber_name is None:
        plugin_class.subscriber_name = subscriber_name

    subscriber_registry.register(subscriber_name, plugin_class)
    logger.debug(f"Registered subscriber plugin: {subscriber_name}")


def get_subscriber_plugin(subscriber_name: str) -> Optional[Type[SubscriberPlugin]]:
    return subscriber_registry.get(subscriber_name)


def create_subscriber(subscriber_name: str, **kwargs) -> Optional[BaseSubscriber]:
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
    subscriber_registry.discover()
    logger.info(f"Discovered {len(subscriber_registry.get_all())} subscriber plugins")


def get_available_subscribers() -> List[str]:
    return list(subscriber_registry.get_all().keys())


def get_subscriber_dependencies(subscriber_name: str) -> List[str]:
    plugin_class = get_subscriber_plugin(subscriber_name)
    if plugin_class is None:
        return []

    return plugin_class.dependencies


def get_subscriber_priority(subscriber_name: str) -> int:
    plugin_class = get_subscriber_plugin(subscriber_name)
    if plugin_class is None:
        return 0

    return plugin_class.priority


def is_subscriber_enabled_by_default(subscriber_name: str) -> bool:
    plugin_class = get_subscriber_plugin(subscriber_name)
    if plugin_class is None:
        return False

    return plugin_class.enabled_by_default
