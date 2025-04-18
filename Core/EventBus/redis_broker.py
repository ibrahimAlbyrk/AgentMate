import json
import asyncio
from typing import Dict, Optional, Any

from redis.asyncio import Redis
from Core.logger import LoggerCreator
from Core.EventBus.message import Message
from Core.EventBus.broker import MessageBroker, MessageCallback, BrokerFactory


class RedisBroker(MessageBroker):
    """
    Redis implementation of the MessageBroker interface.

    This class uses Redis pub/sub for message passing.
    """

    def __init__(self, redis_url: str):
        """
        Initialize the Redis broker.

        Args:
            redis_url: The URL of the Redis server
        """
        self.redis_url = redis_url
        self.redis: Optional[Redis] = None
        self.pubsub = None
        self.subscribers: Dict[str, MessageCallback] = {}
        self.listening_task = None
        self.logger = LoggerCreator.create_advanced_console("RedisBroker")

    async def connect(self) -> None:
        if self.redis is None:
            self.redis = await Redis.from_url(self.redis_url, decode_responses=True)
            self.pubsub = self.redis.pubsub()
            self.logger.debug(f"Connected to Redis at {self.redis_url}")

    async def disconnect(self) -> None:
        if self.redis:
            await self.stop_listening()
            await self.redis.close()
            self.redis = None
            self.pubsub = None
            self.logger.debug("Disconnected from Redis")

    async def publish(self, message: Message) -> None:
        if self.redis is None:
            await self.connect()

        await self.redis.publish(message.topic, message.to_json())
        self.logger.debug(f"Published message to {message.topic}")

    async def subscribe(self, topic: str, callback: MessageCallback) -> None:
        """
        Subscribe to a Redis channel.

        Args:
            topic: The topic (channel) to subscribe to
            callback: The callback to invoke when a message is received
        """
        self.subscribers[topic] = callback

        if self.pubsub:
            await self.pubsub.subscribe(topic)
            self.logger.debug(f"Subscribed to {topic}")

    async def unsubscribe(self, topic: str) -> None:
        """
        Unsubscribe from a Redis channel.

        Args:
            topic: The topic (channel) to unsubscribe from
        """
        if topic in self.subscribers:
            self.subscribers.pop(topic)

            if self.pubsub:
                await self.pubsub.unsubscribe(topic)
                self.logger.debug(f"Unsubscribed from {topic}")

    async def start_listening(self) -> None:
        if self.redis is None:
            await self.connect()

        if not self.subscribers:
            self.logger.warning("No subscribers registered")
            return

        if self.listening_task is not None:
            self.logger.warning("Already listening")
            return

        # Subscribe to all topics
        await self.pubsub.subscribe(*self.subscribers.keys())
        self.logger.debug(f"Subscribed to: {list(self.subscribers.keys())}")

        # Start listening to the task
        self.listening_task = asyncio.create_task(self._listen())
        self.logger.debug("Started listening for messages")

    async def stop_listening(self) -> None:
        if self.listening_task:
            self.listening_task.cancel()
            try:
                await self.listening_task
            except asyncio.CancelledError:
                pass
            self.listening_task = None
            self.logger.debug("Stopped listening for messages")

    async def _listen(self) -> None:
        """
        Listen for messages on subscribed channels.
        """
        try:
            while True:
                message = await self.pubsub.get_message(ignore_subscribe_messages=True)
                if message:
                    channel = message["channel"]
                    data = message["data"]

                    if channel in self.subscribers:
                        try:
                            # Convert the Redis message to the Message object
                            event_message = Message.from_json(data)
                            await self.subscribers[channel](event_message)
                        except Exception as e:
                            self.logger.error(f"Error processing message on {channel}: {str(e)}")

                await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            self.logger.debug("Listening task cancelled")
            raise
        except Exception as e:
            self.logger.error(f"Error in listening task: {str(e)}")
            raise
