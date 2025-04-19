import asyncio
import pkgutil
import inspect
import importlib
import Subscribers

from Core.EventBus import EventBus

from Core.Models import Event
from Core.logger import LoggerCreator
from Core.task_runner import TaskRunner
from Core.agent_manager import AgentManager

from Connectors.omi_connector import OmiConnector

from Subscribers.base_subscriber import BaseSubscriber

logger = LoggerCreator.create_advanced_console("SubscriberManager")

event_bus = EventBus()

async def start_all_subscribers():
    logger.debug("Starting EventBus subscribers...")

    await event_bus.connect()

    shared_services = {
        'omi': OmiConnector(),
        'event_bus': event_bus,
        'task_runner': TaskRunner(),
        "agent_manager": AgentManager()
    }

    for _, module_name, _ in pkgutil.iter_modules(Subscribers.__path__):
        module = importlib.import_module(f"Subscribers.{module_name}")
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and issubclass(obj, BaseSubscriber) and obj is not BaseSubscriber:
                instance = obj()
                await instance.setup(**shared_services)

    await event_bus.listen()

async def stop_all_subscribers():
    await event_bus.stop()
