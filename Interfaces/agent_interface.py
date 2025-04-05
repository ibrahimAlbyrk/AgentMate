from typing import Optional, Coroutine
from Core.config import settings
from abc import ABC, abstractmethod
from composio_openai import ComposioToolSet, App, Action
from DB.Services.user_settings_service import UserSettingsService

from Agents.LLM.llm_agent import LLMAgent

toolset = ComposioToolSet(api_key=settings.COMPOSIO_API_KEY)

class IAgent(ABC):
    def __init__(self, uid: str, service_id, actions: list[str]):
        self.uid = uid
        self.service_id = service_id

        self.entity = toolset.get_entity(uid)
        self.app_name: App = None

        self.llm = LLMAgent(uid, service_id, actions)

        self.listener = toolset.create_trigger_listener()
        self._listener_refs = []

    def add_listener(self, trigger_name: str, handler: callable, config: Optional[dict] = None):
        config = config or {}

        self.entity.enable_trigger(
            app=self.app_name,
            trigger_name=trigger_name,
            config=config
        )

        decorated = self.listener.callback(filters={"trigger_name": trigger_name})(handler)
        self._listener_refs.append(decorated)

    async def run(self):
        await self._run_impl()

    @abstractmethod
    async def _run_impl(self):
       pass

    async def stop(self):
        self.listener.stop()
        del self._listener_refs
        await self._stop_impl()

    @abstractmethod
    async def _stop_impl(self):
        pass
