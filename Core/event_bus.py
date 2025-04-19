import asyncio
from redis.asyncio import Redis
from Core.config import settings
from Core.logger import LoggerCreator
from typing import Callable, Awaitable, Dict

class EventBus:
    def __init__(self):
        self.redis: Redis = None
        self.logger = LoggerCreator.create_advanced_console("EventBus")
        self.redis_url = settings.redis.url
        self.subscribers: Dict[str, Callable[[str], Awaitable[None]]] = {}

    async def connect(self):
        self.redis = await Redis.from_url(self.redis_url, decode_responses=True)

    async def publish(self, channel: str, message: str):
        if self.redis is None:
            await self.connect()
        await self.redis.publish(channel, message)
        # self.logger.debug(f"Published to {channel}: {message}")

    def subscribe(self, channel: str, callback: Callable[[str], Awaitable[None]]):
        self.subscribers[channel] = callback

    async def listen(self):
        if self.redis is None:
            await self.connect()

        pubsub = self.redis.pubsub()
        await pubsub.subscribe(*self.subscribers.keys())
        self.logger.debug(f"Subscribed to: {self.subscribers.keys()}")
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                channel = message["channel"]
                data = message["data"]
                # self.logger.debug(f"Received message on {channel}: {data}")
                if channel in self.subscribers:
                    try:
                        await self.subscribers[channel](data)
                    except Exception as e:
                        self.logger.error(f"Error while processing message on {channel}: {str(e)}")
            await asyncio.sleep(0.01)
