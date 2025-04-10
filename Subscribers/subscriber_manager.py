import asyncio
import pkgutil
import inspect
import importlib

from Core.event_bus import EventBus
from Core.logger import LoggerCreator

import Subscribers
from Subscribers.base_subscriber import BaseSubscriber

logger = LoggerCreator.create_advanced_console("SubscriberManager")
event_bus = EventBus()

async def start_all_subscribers():

    logger.debug("Starting EventBus subscribers...")
    for _, module_name, _ in pkgutil.iter_modules(Subscribers.__path__):
        module = importlib.import_module(f"Subscribers.{module_name}")
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and issubclass(obj, BaseSubscriber) and obj is not BaseSubscriber:
                instance = obj()
                asyncio.create_task(instance.setup())

def stop_all_subscribers():
    if event_bus.redis:
        logger.debug("Shutting down EventBus and task pool...")
        event_bus.redis.close()