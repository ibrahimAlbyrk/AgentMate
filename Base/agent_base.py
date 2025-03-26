from Core.logger import LoggerCreator
from Interfaces.agent_interface import IAgent

class BaseAgent(IAgent):
    def __init__(self, name: str):
        self.logger = LoggerCreator.create_advanced_console(name)

    async def run(self, uid: str):
        raise NotImplementedError("run() method must be implemented by the subclass")