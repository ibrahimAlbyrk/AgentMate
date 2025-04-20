from abc import abstractmethod, ABC
from typing import Dict, Type, Optional, Any, List

from Core.logger import LoggerCreator
from Plugins.plugin_interface import IPlugin
from Plugins.plugin_system import plugin_manager, PluginRegistry

logger = LoggerCreator.create_advanced_console("SubscriberPlugin")


class SubscriberPlugin(IPlugin, ABC):
    """
    Base class for subscriber plugins.

    Subscriber plugins are responsible for creating and configuring
    subscriber instances for specific event types.
    """
    name: str = None

    priority: int = 0

    dependencies: List[str] = []

    enabled_by_default: bool = True

    @classmethod
    @abstractmethod
    def create(cls, **kwargs) -> IPlugin:
        return cls()

    @classmethod
    def get_config_schema(cls) -> Dict[str, Any]:
        return {}

    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> bool:
        return True


subscriber_registry: PluginRegistry[Type[SubscriberPlugin]] = plugin_manager.create_registry(
    SubscriberPlugin, ["Subscribers"]
)
