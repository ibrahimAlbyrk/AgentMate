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
    async def register(self):
        self.event_bus.subscribe("agent.start", _handle_agent_start)
        self.event_bus.subscribe("agent.start_all", _handle_agent_start_all)

        self.event_bus.subscribe("agent.stop", _handle_agent_stop)
        self.event_bus.subscribe("agent.stop_all", _handle_agent_stop_all)

        self.event_bus.subscribe("agent.restart", _handle_agent_restart)


async def _handle_agent_start_all(raw_data: str):
    data = _try_get_all_services(raw_data)
    if not data:
        return

    uid = data.get("uid")
    service_id = data.get("service_id")
    services = data.get("services")

    await agent_manager.start_all_for_user(uid, service_id, services)


async def _handle_agent_stop_all(raw_data: str):
    uid = _try_get_uid(raw_data)
    if not uid:
        return

    await agent_manager.stop_all_for_user(uid)


async def _handle_agent_start(raw_data: str):
    await _handle_agent_restart(raw_data)


async def _handle_agent_stop(raw_data: str):
    data = _try_get_data(raw_data)
    if not data:
        return

    uid = data.uid
    service = data.service

    is_running = agent_manager.is_running(uid, service)
    if is_running:
        await agent_manager.stop_agent(uid, service)


async def _handle_agent_restart(raw_data: str):
    data = _try_get_data(raw_data)
    if not data:
        return

    uid = data.uid
    service_id = data.service_id
    service = data.service

    is_running = agent_manager.is_running(uid, service)
    if is_running:
        await agent_manager.restart_agent(uid, service_id, service)
    else:
        await agent_manager.start_agent(uid, service_id, service)


def _try_get_all_services(raw_data: str) -> dict:
    try:
        payload = json.loads(raw_data)
        uid = payload["uid"]
        services = payload["services"]
        return {"uid": uid, "services": services}
    except Exception as e:
        logger.error(f"Error handling agent services data: {str(e)}")
        return None


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


def _try_get_uid(raw_data: str) -> str:
    try:
        payload = json.loads(raw_data)
        uid = payload["uid"]
        return uid
    except Exception as e:
        logger.error(f"Error handling agent uid data: {str(e)}")
        return None
