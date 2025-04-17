from abc import ABC, abstractmethod
from typing import Optional, Coroutine, Any

from composio_openai import ComposioToolSet, App, Action

from Core.config import settings
from Core.logger import LoggerCreator

from Agents.LLM.llm_agent import LLMAgent, LLMActionData

from DB.Services.user_settings_service import UserSettingsService

class IAgent(ABC):
    def __init__(self, uid: str, service_id):
        self.uid = uid
        self.service_id = service_id

        self.actions: dict[str, LLMActionData] = {}
        self.llm: LLMAgent = None

        self.toolset = ComposioToolSet(api_key=settings.COMPOSIO_API_KEY)

        self.entity = self.toolset.get_entity(uid)
        self.app_name: App = None

        self.listener = self.toolset.create_trigger_listener()
        self._listener_refs = []

        self.logger = LoggerCreator.create_advanced_console(self.__class__.__name__)

    def initialize(self, actions: dict[str, LLMActionData] = []):
        self.actions = actions
        self.llm = LLMAgent(self.app_name, self.uid, self.service_id, self.toolset, actions)

    def add_listener(self, trigger_name: str, handler, config: Optional[dict] = None):
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
        # self.listener.stop()
        del self._listener_refs
        await self._stop_impl()

    @abstractmethod
    async def _stop_impl(self):
        pass
