import json

from Core.event_bus import EventBus
from Core.logger import LoggerCreator
from Core.agent_manager import AgentManager

from Subscribers.base_subscriber import BaseSubscriber

logger = LoggerCreator.create_advanced_console("AgentSubscriber")

event_bus = EventBus()
agent_manager = AgentManager()


class AgentEventData:
    def __init__(self, uid: str, service: str):
        self.uid = uid
        self.service = service


class AgentSubscriber(BaseSubscriber):
    async def register(self):
        self.event_bus.subscribe("agent.start", _handle_agent_start)
        self.event_bus.subscribe("agent.start_all", _handle_agent_start_all)

        self.event_bus.subscribe("agent.stop", _handle_agent_stop)
        self.event_bus.subscribe("agent.stop_all", _handle_agent_stop_all)

        self.event_bus.subscribe("agent.restart", _handle_agent_restart)


def _handle_agent_start_all(raw_data: str):
    data = _try_get_data(raw_data)
    if not data:
        return

    agent_manager.start_all_for_user(uid, service)


def _handle_agent_stop_all(raw_data: str):
    uid = _try_get_uid(raw_data)
    if not uid:
        return

    agent_manager.stop_all_for_user(uid)


def _handle_agent_start(raw_data: str):
    data = _try_get_data(raw_data)
    if not data:
        return

    is_running = agent_manager.is_running(uid, service)
    if is_running:
        agent_manager.restart_agent(uid, service)
    else:
        agent_manager.start_agent(uid, service)


def _handle_agent_stop(raw_data: str):
    data = _try_get_data(raw_data)
    if not data:
        return

    is_running = agent_manager.is_running(uid, service)
    if is_running:
        agent_manager.stop_agent(uid, service)


def _handle_agent_restart(raw_data: str):
    data = _try_get_data(raw_data)
    if not data:
        return

    is_running = agent_manager.is_running(uid, service)
    if is_running:
        agent_manager.restart_agent(uid, service)
    else:
        agent_manager.start_agent(uid, service)


def _try_get_data(raw_data: str) -> AgentEventData:
    try:
        payload = json.loads(raw_data)
        uid = payload["uid"]
        service = payload["service"]
        return AgentEventData(uid, service)
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
