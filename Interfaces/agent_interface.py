from abc import ABC, abstractmethod

class IAgent(ABC):
    @abstractmethod
    async def run(self, uid: str):
        pass

    @abstractmethod
    async def stop(self, uid: str):
        pass