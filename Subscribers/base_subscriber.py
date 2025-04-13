from abc import ABC, abstractmethod
from Core.event_bus import EventBus

class BaseSubscriber(ABC):
    @abstractmethod
    async def setup(self, **services):
        raise NotImplementedError
