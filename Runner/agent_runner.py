import asyncio
from Core.logger import LoggerCreator
from Interfaces.agent_interface import IAgent

class AgentRunner:
    def __init__(self, agents: list[IAgent]):
        self.agents = agents
        self.logger = LoggerCreator.create_advanced_console("AgentRunner")

    async def start_all(self, uid: str):
        tasks = [agent.run(uid) for agent in self.agents]
        self.logger.info(f"Starting {len(tasks)} agents for uid {uid}")
        await asyncio.gather(*tasks)