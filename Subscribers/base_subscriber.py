from abc import ABC, abstractmethod
from Core.event_bus import EventBus

class BaseSubscriber(ABC):
    def __init__(self):
        self.event_bus = EventBus()

    @abstractmethod
    async def register(self):
        pass

    async def setup(self):
        await self.event_bus.connect()
        await self.register()
        await self.event_bus.listen()