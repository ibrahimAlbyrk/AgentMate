"""
EventBus implementation for AgentMate.

This module provides the main EventBus class that serves as the entry point
for the event-driven communication system.
"""

import asyncio
from typing import Dict, Optional, Any, Callable, Awaitable, List, Type

from Core.logger import LoggerCreator
from Core.config import settings
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
        """
        Connect to the message broker.
        """
        await self.broker.connect()
    
    async def disconnect(self) -> None:
        """
        Disconnect from the message broker.
        """
        await self.broker.disconnect()
    
    async def publish(self, topic: str, payload: Any, **metadata) -> None:
        """
        Publish a message to a topic.
        
        Args:
            topic: The topic to publish to
            payload: The payload of the message
            **metadata: Additional metadata for the message
        """
        message = Message.create(topic, payload, **metadata)
        await self.broker.publish(message)
    
    def subscribe(self, topic: str, callback: Callable[[Any], Awaitable[None]]) -> None:
        """
        Subscribe to a topic.
        
        Args:
            topic: The topic to subscribe to
            callback: The callback to invoke when a message is received
        """
        # Store the original callback for type checking
        self._callbacks[topic] = callback
        
        # Create a wrapper that extracts the payload
        async def wrapper(message: Message) -> None:
            try:
                await callback(message.payload)
            except Exception as e:
                self.logger.error(f"Error in callback for {topic}: {str(e)}")
        
        # Subscribe with the wrapper
        asyncio.create_task(self.broker.subscribe(topic, wrapper))
        self.logger.debug(f"Subscribed to {topic}")
    
    async def unsubscribe(self, topic: str) -> None:
        """
        Unsubscribe from a topic.
        
        Args:
            topic: The topic to unsubscribe from
        """
        await self.broker.unsubscribe(topic)
        self._callbacks.pop(topic, None)
        self.logger.debug(f"Unsubscribed from {topic}")
    
    async def listen(self) -> None:
        """
        Start listening for messages.
        """
        await self.broker.start_listening()
    
    async def stop(self) -> None:
        """
        Stop listening for messages and disconnect.
        """
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