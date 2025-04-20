from typing import Dict, Type, Optional, Any, List

from Core.logger import LoggerCreator
from Agents.agent_interface import IAgent
from Plugins.plugin_interface import IPlugin
from Plugins.plugin_system import plugin_manager, PluginRegistry

logger = LoggerCreator.create_advanced_console("AgentPlugin")


class AgentPlugin(IPlugin):
    """
    Base class for agent plugins.

    Agent plugins are responsible for creating and configuring
    agent instances for specific services.
    """
    name: str = None

    priority: int = 0

    dependencies: List[str] = []

    enabled_by_default: bool = True

    @classmethod
    def create(cls, **kwargs) -> Optional[IAgent]:
        raise NotImplementedError("Agent plugins must implement create_agent")

    @classmethod
    def get_config_schema(cls) -> Dict[str, Any]:
        return {}

    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> bool:
        return True


agent_registry: PluginRegistry[Type[AgentPlugin]] = plugin_manager.create_registry(
    AgentPlugin, ["Agents"]
)
