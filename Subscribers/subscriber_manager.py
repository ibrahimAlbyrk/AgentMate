from Core.EventBus import EventBus
from Core.logger import LoggerCreator
from Core.task_runner import TaskRunner
from Connectors.omi_connector import OmiConnector

from Plugins import plugin_utils
from Plugins.plugin_interface import IPlugin
from Plugins.subscriber_plugin import subscriber_registry


logger = LoggerCreator.create_advanced_console("SubscriberManager")
event_bus = EventBus()

async def start_all_subscribers():
    logger.debug("Starting plugin-based EventBus subscribers...")

    await event_bus.connect()

    shared_services = {
        "omi": OmiConnector(),
        "event_bus": event_bus,
        "task_runner": TaskRunner()
    }

    plugin_utils.discover_plugins(subscriber_registry, "Subscribers")

    subscribers = plugin_utils.get_all_plugins(subscriber_registry)

    for name in subscribers:
        deps = plugin_utils.get_plugin_dependencies(name, subscriber_registry)
        services = {k: v for k, v in shared_services.items() if k in deps}

        try:
            await plugin_utils.create_plugin(name, subscriber_registry, **services)
            logger.debug(f"Started subscriber: {name}")
        except Exception as e:
            logger.warning(f"Failed to start subscriber: {e}")

    await event_bus.listen()


async def stop_all_subscribers():
    await event_bus.stop()
