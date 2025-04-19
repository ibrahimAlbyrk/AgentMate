import json

from Core.EventBus import EventBus
from Core.logger import LoggerCreator
from Core.agent_manager import AgentManager
from Core.Models.domain import EventType, Event

from Subscribers.base_subscriber import BaseSubscriber
from Subscribers.subscriber_plugin import SubscriberPlugin, register_subscriber_plugin

logger = LoggerCreator.create_advanced_console("AgentSubscriber")


class AgentSubscriber(BaseSubscriber, SubscriberPlugin):
    subscriber_name = "agent"
    priority = 100
    dependencies = ["event_bus", "agent_manager"]
    enabled_by_default = True

    def __init__(self):
        self.event_bus = None
        self.agent_manager: AgentManager = None

    async def setup(self, **services):
        self.event_bus = services["event_bus"]
        self.agent_manager = services["agent_manager"]

        await self.event_bus.subscribe(EventType.START_AGENT, self._handle_agent_start)
        await self.event_bus.subscribe(EventType.START_ALL_AGENT, self._handle_agent_start_all)

        await self.event_bus.subscribe(EventType.STOP_AGENT, self._handle_agent_stop)
        await self.event_bus.subscribe(EventType.STOP_ALL_AGENT, self._handle_agent_stop_all)

        await self.event_bus.subscribe(EventType.RESTART_AGENT, self._handle_agent_restart)

    async def _handle_agent_start_all(self, event: Event):
        try:
            data = event.data
            uid = data["uid"]
            services = data["services"]

            await self.agent_manager.start_all_for_user(uid, services)
        except Exception as e:
            logger.error(f"Start all agents error: {str(e)}")

    async def _handle_agent_stop_all(self, event: Event):
        try:
            data = event.data
            uid = data["uid"]
            await self.agent_manager.stop_all_for_user(uid)
        except Exception as e:
            logger.error(f"Stop all agents error: {str(e)}")

    async def _handle_agent_start(self, event: Event):
        await self._handle_agent_restart(event)

    async def _handle_agent_stop(self, event: Event):
        try:
            data = event.data
            uid = data["uid"]
            service = data["service"]

            if self.agent_manager.is_running(uid, service):
                await self.agent_manager.stop_agent(uid, service)
        except Exception as e:
            logger.error(f"Stop agent error: {str(e)}")

    async def _handle_agent_restart(self, event: Event):
        try:
            data = event.data
            uid = data["uid"]
            service = data["service"]

            if self.agent_manager.is_running(uid, service):
                await self.agent_manager.restart_agent(uid, service)
            else:
                await self.agent_manager.start_agent(uid, service)

        except Exception as e:
            logger.error(f"Restart agent error: {str(e)}")

    @classmethod
    def create_subscriber(cls, **kwargs) -> BaseSubscriber:
        return cls()


register_subscriber_plugin("agent", AgentSubscriber)
