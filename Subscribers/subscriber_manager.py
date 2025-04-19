import asyncio
from Core.EventBus import EventBus
from Core.logger import LoggerCreator
from Core.task_runner import TaskRunner
from Core.agent_manager import AgentManager
from Connectors.omi_connector import OmiConnector

from Subscribers.subscriber_plugin import (
    discover_subscriber_plugins,
    get_available_subscribers,
    create_subscriber,
    get_subscriber_dependencies,
)

logger = LoggerCreator.create_advanced_console("SubscriberManager")
event_bus = EventBus()

async def start_all_subscribers():
    logger.debug("Starting plugin-based EventBus subscribers...")

    await event_bus.connect()

    shared_services = {
        "omi": OmiConnector(),
        "event_bus": event_bus,
        "task_runner": TaskRunner(),
        "agent_manager": AgentManager()
    }

    discover_subscriber_plugins()

    for name in get_available_subscribers():
        deps = get_subscriber_dependencies(name)
        services = {k: v for k, v in shared_services.items() if k in deps}

        subscriber = create_subscriber(name)
        if subscriber is not None:
            await subscriber.setup(**services)
            logger.debug(f"Started subscriber: {name}")
        else:
            logger.warning(f"Failed to start subscriber: {name}")

    await event_bus.listen()


async def stop_all_subscribers():
    await event_bus.stop()
