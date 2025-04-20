from Core.logger import LoggerCreator
from Core.agent_factory import AgentFactory

from Agents.agent_interface import IAgent

from typing import ClassVar
from typing import TypeVar, Type, cast

from asyncio import wait_for, gather

T_agent = TypeVar('T_agent', bound=IAgent)

class AgentManager:
    _instance: ClassVar["AgentManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AgentManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.logger = LoggerCreator.create_advanced_console("AgentManager")
        self.running_agents: dict[str, dict[str, IAgent]] = {}
        """ {uid: {service_name: agent}} """

    def get_agent(self, uid: str, agent_name: str, agent_type: Type[T_agent]) -> T_agent:
        agents = self.running_agents.get(uid, {})
        agent = agents.get(agent_name, None)
        if isinstance(agent, agent_type):
            return cast(T_agent, agent)
        return None

    async def start_agent(self, uid: str, service: str):
        agent = AgentFactory.create(uid, service)
        if not agent:
            self.logger.warning(f"No agent registered for {service} service")
            return

        self.running_agents.setdefault(uid, {})
        if service in self.running_agents[uid]:
            self.logger.debug(f"Agent for {service} already running for {uid}")
            return

        await agent.run()
        self.running_agents[uid][service] = agent
        self.logger.debug(f"Started {service} agent for {uid}")

    async def stop_agent(self, uid: str, service: str):
        agent = self.running_agents.get(uid, {}).get(service)
        if not agent:
            self.logger.warning(f"No running agent for {uid}/{service} to stop")
            return

        try:
            if hasattr(agent, "stop") and callable(getattr(agent, "stop")):
                await wait_for(agent.stop(), timeout=3)
                self.logger.debug(f"Stopped {service} agent for {uid}")
            else:
                self.logger.warning(f"{service} agent has no stop() method")
        except Exception as e:
            self.logger.error(f"[{uid}] Failed to stop {service} agent: {str(e)}")

        self.running_agents[uid].pop(service, None)
        if not self.running_agents[uid]:
            self.running_agents.pop(uid, None)

    async def restart_agent(self, uid: str, service: str):
        self.logger.debug(f"Restarting {service} agent for {uid}")
        await self.stop_agent(uid, service)
        await self.start_agent(uid, service)

    async def start_all_for_user(self, uid: str, services: list[str]):
        for service in services:
            await self.start_agent(uid, service)

    async def stop_all_for_user(self, uid: str):
        services = list(self.running_agents.get(uid, {}).keys())

        tasks = [self._stop_agent_safe(uid, service) for service in services]
        await gather(*tasks)

    async def _stop_agent_safe(self, uid: str, service: str):
        try:
            await self.stop_agent(uid, service)
        except Exception as e:
            self.logger.error(f"[{uid}] Unexpected error stopping {service} agent: {str(e)}")

    def is_running(self, uid: str, service: str):
        return uid in self.running_agents and service in self.running_agents[uid]
