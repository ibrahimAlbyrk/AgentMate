from typing import Optional

from Core.logger import LoggerCreator
from Core.agent_manager import AgentManager
from Core.Models.domain import EventType, Event

from Plugins.plugin_interface import IPlugin
from Plugins.subscriber_plugin import SubscriberPlugin

logger = LoggerCreator.create_advanced_console("AgentSubscriber")


class AgentSubscriber(SubscriberPlugin):
    name = "agent"
    priority = 100
    dependencies = ["event_bus", "agent_manager"]
    enabled_by_default = True

    def __init__(self):
        self.event_bus = None
        self.agent_manager: AgentManager = None

    @classmethod
    async def create(cls, **kwargs) -> IPlugin:
        instance = cls()

        instance.event_bus = kwargs["event_bus"]
        instance.agent_manager = kwargs["agent_manager"]

        await instance.event_bus.subscribe(EventType.START_AGENT, instance._handle_agent_start)
        await instance.event_bus.subscribe(EventType.START_ALL_AGENT, instance._handle_agent_start_all)

        await instance.event_bus.subscribe(EventType.STOP_AGENT, instance._handle_agent_stop)
        await instance.event_bus.subscribe(EventType.STOP_ALL_AGENT, instance._handle_agent_stop_all)

        await instance.event_bus.subscribe(EventType.RESTART_AGENT, instance._handle_agent_restart)

        return instance

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

            async def stop():
                if self.agent_manager.is_running(uid, service):
                    await self.agent_manager.stop_agent(uid, service)

            asyncio.create_task(stop())

        except Exception as e:
            logger.error(f"Stop agent error: {str(e)}")

    async def _handle_agent_restart(self, event: Event):
        try:
            data = event.data
            uid = data["uid"]
            service = data["service"]

            async def restart():
                if self.agent_manager.is_running(uid, service):
                    await self.agent_manager.restart_agent(uid, service)
                else:
                    await self.agent_manager.start_agent(uid, service)

            asyncio.create_task(restart())

        except Exception as e:
            logger.error(f"Restart agent error: {str(e)}")
