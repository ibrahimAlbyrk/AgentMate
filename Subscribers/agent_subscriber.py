import json

from Core.event_bus import EventBus
from Core.logger import LoggerCreator
from Core.agent_manager import AgentManager

from Subscribers.base_subscriber import BaseSubscriber

logger = LoggerCreator.create_advanced_console("AgentSubscriber")

event_bus = EventBus()
agent_manager = AgentManager()


class AgentEventData:
    def __init__(self, uid: str, service_id: str, service: str):
        self.uid = uid
        self.service_id = service_id
        self.service = service


class AgentSubscriber(BaseSubscriber):
    def __init__(self):
        self.event_bus = None
        self.agent_manager = None

    async def setup(self, **services):
        self.event_bus = services["event_bus"]
        self.agent_manager = services["agent_manager"]

        self.event_bus.subscribe("agent.start", self._handle_agent_start)
        self.event_bus.subscribe("agent.start_all", self._handle_agent_start_all)

        self.event_bus.subscribe("agent.stop", self._handle_agent_stop)
        self.event_bus.subscribe("agent.stop_all", self._handle_agent_stop_all)

        self.event_bus.subscribe("agent.restart", self._handle_agent_restart)

    async def _handle_agent_start_all(self, raw_data: str):
        try:
            payload = json.loads(raw_data)
            uid = payload.get("uid")
            service_id = payload.get("service_id")
            services = payload.get("services")

            await self.agent_manager.start_all_for_user(uid, service_id, services)
        except Exception as e:
            logger.error(f"Start all agents error: {str(e)}")

    async def _handle_agent_stop_all(self, raw_data: str):
        try:
            payload = json.loads(raw_data)
            uid = payload.get("uid")
            await self.agent_manager.stop_all_for_user(uid)
        except Exception as e:
            logger.error(f"Stop all agents error: {str(e)}")

    async def _handle_agent_start(self, raw_data: str):
        await self._handle_agent_restart(raw_data)

    async def _handle_agent_stop(self, raw_data: str):
        try:
            payload = json.loads(raw_data)
            uid = payload["uid"]
            service = payload["service"]

            if self.agent_manager.is_running(uid, service):
                await self.agent_manager.stop_agent(uid, service)
        except Exception as e:
            logger.error(f"Stop agent error: {str(e)}")

    async def _handle_agent_restart(self, raw_data: str):
        try:
            payload = json.loads(raw_data)
            uid = payload["uid"]
            service_id = payload.get("service_id", "")
            service = payload["service"]

            if self.agent_manager.is_running(uid, service):
                await self.agent_manager.restart_agent(uid, service_id, service)
            else:
                await self.agent_manager.start_agent(uid, service_id, service)

        except Exception as e:
            logger.error(f"Restart agent error: {str(e)}")

    @staticmethod
    def _try_get_all_services(raw_data: str) -> dict:
        try:
            payload = json.loads(raw_data)
            uid = payload["uid"]
            services = payload["services"]
            return {"uid": uid, "services": services}
        except Exception as e:
            logger.error(f"Error handling agent services data: {str(e)}")
            return None

    @staticmethod
    def _try_get_data(raw_data: str) -> AgentEventData:
        try:
            payload = json.loads(raw_data)
            uid = payload["uid"]
            service_id = payload.get("service_id", "")
            service = payload["service"]
            return AgentEventData(uid, service_id, service)
        except Exception as e:
            logger.error(f"Error handling agent data: {str(e)}")
            return None

    @staticmethod
    def _try_get_uid(raw_data: str) -> str:
        try:
            payload = json.loads(raw_data)
            uid = payload["uid"]
            return uid
        except Exception as e:
            logger.error(f"Error handling agent uid data: {str(e)}")
            return None
