"""
Subscriber Manager for AgentMate

This module provides functions for managing subscribers using the
subscriber plugin system.
"""

import asyncio
from typing import Dict, List, Any, Optional, Set

from Core.EventBus import EventBus
from Core.logger import LoggerCreator
from Core.task_runner import TaskRunner
from Core.agent_manager import AgentManager
from Core.dependency_injection import container

from Connectors.omi_connector import OmiConnector

from Subscribers.base_subscriber import BaseSubscriber
from Core.subscriber_plugin import (
    discover_subscriber_plugins, get_available_subscribers,
    get_subscriber_dependencies, get_subscriber_priority,
    is_subscriber_enabled_by_default, create_subscriber
)

logger = LoggerCreator.create_advanced_console("SubscriberManager")

# Global instances
event_bus = EventBus()
_running_subscribers: Dict[str, BaseSubscriber] = {}


async def initialize_subscriber_system():
    """
    Initialize the subscriber system.

    This function discovers and registers all subscriber plugins.
    """
    # Register services with the dependency injection container
    container.register_singleton(EventBus, event_bus)
    container.register_singleton(TaskRunner)
    container.register_singleton(AgentManager)
    container.register_singleton(OmiConnector)

    # Discover subscriber plugins
    discover_subscriber_plugins()
    logger.info(f"Available subscribers: {get_available_subscribers()}")


async def start_all_subscribers():
    """
    Start all subscribers in the correct order based on dependencies and priority.
    """
    logger.debug("Starting EventBus subscribers...")

    # Connect to the event bus
    await event_bus.connect()

    # Initialize the subscriber system if not already initialized
    if not get_available_subscribers():
        await initialize_subscriber_system()

    # Get all available subscribers
    available_subscribers = get_available_subscribers()

    # Start subscribers in the correct order
    await start_subscribers_in_order(available_subscribers)

    # Start listening for events
    asyncio.create_task(event_bus.listen())

    logger.info(f"Started {len(_running_subscribers)} subscribers")


async def start_subscribers_in_order(subscriber_names: List[str]) -> None:
    """
    Start subscribers in the correct order based on dependencies and priority.

    Args:
        subscriber_names: The names of the subscribers to start
    """
    # Sort subscribers by priority (higher priority first)
    sorted_subscribers = sorted(
        subscriber_names,
        key=lambda name: get_subscriber_priority(name),
        reverse=True
    )

    # Track started subscribers
    started: Set[str] = set()

    # Start subscribers in order
    for name in sorted_subscribers:
        await start_subscriber_with_dependencies(name, started)


async def start_subscriber_with_dependencies(name: str, started: Set[str]) -> None:
    """
    Start a subscriber and its dependencies.

    Args:
        name: The name of the subscriber to start
        started: A set of already started subscriber names
    """
    # Skip if already started
    if name in started:
        return

    # Skip if not enabled by default
    if not is_subscriber_enabled_by_default(name):
        logger.debug(f"Skipping disabled subscriber: {name}")
        return

    # Start dependencies first
    dependencies = get_subscriber_dependencies(name)
    for dep in dependencies:
        await start_subscriber_with_dependencies(dep, started)

    # Start the subscriber
    await start_subscriber(name)

    # Mark as started
    started.add(name)


async def start_subscriber(name: str) -> Optional[BaseSubscriber]:
    """
    Start a single subscriber.

    Args:
        name: The name of the subscriber to start

    Returns:
        The started subscriber instance or None if startup fails
    """
    # Skip if already running
    if name in _running_subscribers:
        logger.debug(f"Subscriber already running: {name}")
        return _running_subscribers[name]

    # Create the subscriber instance
    subscriber = create_subscriber(name)
    if not subscriber:
        logger.warning(f"Failed to create subscriber: {name}")
        return None

    try:
        # Get services from the dependency injection container
        services = {
            'event_bus': container.resolve(EventBus),
            'task_runner': container.resolve(TaskRunner),
            'agent_manager': container.resolve(AgentManager),
            'omi': container.resolve(OmiConnector)
        }

        # Set up the subscriber
        await subscriber.setup(**services)

        # Store the running subscriber
        _running_subscribers[name] = subscriber

        logger.debug(f"Started subscriber: {name}")
        return subscriber

    except Exception as e:
        logger.error(f"Error starting subscriber {name}: {str(e)}")
        return None


async def stop_subscriber(name: str) -> None:
    """
    Stop a single subscriber.

    Args:
        name: The name of the subscriber to stop
    """
    if name not in _running_subscribers:
        logger.debug(f"Subscriber not running: {name}")
        return

    subscriber = _running_subscribers[name]

    try:
        # Call stop method if it exists
        if hasattr(subscriber, "stop") and callable(getattr(subscriber, "stop")):
            await subscriber.stop()

        # Remove from running subscribers
        _running_subscribers.pop(name)

        logger.debug(f"Stopped subscriber: {name}")

    except Exception as e:
        logger.error(f"Error stopping subscriber {name}: {str(e)}")


async def stop_all_subscribers():
    """
    Stop all running subscribers.
    """
    logger.debug("Stopping all subscribers...")

    # Get a list of running subscribers
    running = list(_running_subscribers.keys())

    # Stop each subscriber
    for name in running:
        await stop_subscriber(name)

    # Disconnect from the event bus
    if event_bus:
        await event_bus.disconnect()

    logger.info("All subscribers stopped")
