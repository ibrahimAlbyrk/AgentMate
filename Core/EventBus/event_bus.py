import asyncio
from typing import Dict, Optional, Any, Callable, Awaitable, List, Type

from Core.config import settings
from Core.Models.domain import Event
from Core.logger import LoggerCreator
from Core.EventBus.message import Message
from Core.EventBus.broker import MessageBroker, BrokerFactory, MessageCallback


class EventBus:
    """
    EventBus for message-based communication between components.

    This class provides a unified interface for publishing and subscribing
    to events using different message broker implementations.
    """
    _instance = None

    def __new__(cls, broker_type: str = None, **broker_kwargs):
        """
        Create a new EventBus instance or return the existing one.

        Args:
            broker_type: The type of broker to use (default: from settings)
            **broker_kwargs: Additional arguments to pass to the broker

        Returns:
            EventBus: The EventBus instance
        """
        if cls._instance is None:
            cls._instance = super(EventBus, cls).__new__(cls)
            cls._instance._initialize(broker_type, **broker_kwargs)
        return cls._instance

    def _initialize(self, broker_type: str = None, **broker_kwargs):
        """
        Initialize the EventBus.

        Args:
            broker_type: The type of broker to use
            **broker_kwargs: Additional arguments to pass to the broker
        """
        self.logger = LoggerCreator.create_advanced_console("EventBus")

        # Use Redis as the default broker if not specified
        broker_type = broker_type or "redis"

        # Create broker instance
        if broker_type == "redis" and not broker_kwargs:
            # Use Redis URL from settings if not provided
            broker_kwargs = {"redis_url": settings.redis.url}

        self.broker: MessageBroker = BrokerFactory.create(broker_type, **broker_kwargs)
        self.logger.debug(f"Initialized EventBus with {broker_type} broker")

        # Track callbacks for type checking and conversion
        self._callbacks: Dict[str, Callable[[Any], Awaitable[None]]] = {}

    async def connect(self) -> None:
        await self.broker.connect()

    async def disconnect(self) -> None:
        await self.broker.disconnect()

    async def publish(self, topic: str, payload: Any, **metadata) -> None:
        """
        Args:
            topic: The topic to publish to
            payload: The payload of the message
            **metadata: Additional metadata for the message
        """
        message = Message.create(topic, payload, **metadata)
        await self.broker.publish(message)

    async def publish_event(self, event: Event) -> None:
        """
        Publish a structured Event directly.

        Args:
            event: Event object to be published
        """
        await self.publish(topic=event.type, payload=event)

    async def subscribe(self, topic: str, callback: Callable[[Any], Awaitable[None]]) -> None:
        """
        Args:
            topic: The topic to subscribe to
            callback: The callback to invoke when a message is received
        """
        # Store the original callback for type checking
        self._callbacks[topic] = callback

        # Create a wrapper that extracts the payload
        async def wrapper(message: Message) -> None:
            try:
                if isinstance(message.payload, dict) and "data" in message.payload and "source" in message.payload:
                    event_obj = Event(**message.payload)
                    await callback(event_obj)
                else:
                    await callback(message.payload)
            except Exception as e:
                self.logger.error(f"Error in callback for {topic}: {str(e)}")

        # Subscribe with the wrapper
        await self.broker.subscribe(topic, wrapper)

    async def unsubscribe(self, topic: str) -> None:
        """
        Args:
            topic: The topic to unsubscribe from
        """
        await self.broker.unsubscribe(topic)
        self._callbacks.pop(topic, None)

    async def listen(self) -> None:
        await self.broker.start_listening()

    async def stop(self) -> None:
        await self.broker.stop_listening()
        await self.broker.disconnect()

    @property
    def subscribed_topics(self) -> List[str]:
        """
        Get a list of subscribed topics.

        Returns:
            List[str]: A list of subscribed topics
        """
        return list(self._callbacks.keys())