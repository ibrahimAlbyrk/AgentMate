from typing import Type, Optional, Any, List

from Core.logger import LoggerCreator
from Plugins.plugin_interface import IPlugin

logger = LoggerCreator.create_advanced_console("PluginUtils")


def register_plugin(name: str, plugin_class: IPlugin, registry):
    if getattr(plugin_class, "name", None) is None:
        setattr(plugin_class, "name", name)
    registry.register(name, plugin_class)


def get_plugin(name: str, registry) -> Optional[IPlugin]:
    return registry.get(name)


async def create_plugin(name: str, registry, **kwargs) -> Optional[IPlugin]:
    plugin_class = get_plugin(name, registry)
    if plugin_class is None:
        logger.warning(f"No plugin found for: {name}")
        return None
    try:
        return await plugin_class.create(**kwargs)
    except Exception as e:
        logger.error(f"Failed to create plugin {name}: {str(e)}")
        return None


def discover_plugins(registry, plugin_type: str = "plugin"):
    registry.discover()
    logger.debug(f"Discovered {len(registry.get_all())} {plugin_type} plugins")


def get_all_plugins(registry) -> List[str]:
    return list(registry.get_all().keys())


def get_plugin_dependencies(name: str, registry) -> List[str]:
    plugin_class = get_plugin(name, registry)
    return getattr(plugin_class, "dependencies", []) if plugin_class else []


def get_plugin_priority(name: str, registry) -> int:
    plugin_class = get_plugin(name, registry)
    return getattr(plugin_class, "priority", 0) if plugin_class else 0


def is_plugin_enabled_by_default(name: str, registry) -> bool:
    plugin_class = get_plugin(name, registry)
    return getattr(plugin_class, "enabled_by_default", True) if plugin_class else False
