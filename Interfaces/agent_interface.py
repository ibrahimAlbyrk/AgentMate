import asyncio

from abc import ABC, abstractmethod
from typing import Optional, Coroutine, Any

from composio_openai import ComposioToolSet, App, Action

from Core.config import settings
from Core.logger import LoggerCreator

from Agents.LLM.llm_agent import LLMAgent, LLMActionData

from DB.Services.user_settings_service import UserSettingsService

class IAgent(ABC):
    def __init__(self, uid: str):
        self.logger = LoggerCreator.create_advanced_console(self.__class__.__name__)

        self.uid = uid

        self.actions: dict[str, LLMActionData] = {}
        self.llm: LLMAgent = None

        self.toolset = ComposioToolSet(api_key=settings.api.composio_api_key)

        self.entity = self.toolset.get_entity(uid)
        self.app_name: App = None

        try:
            self.listener = self.toolset.create_trigger_listener(timeout=5)
        except TimeoutError as e:
            self.listener = None
            self.logger.warning(f"Couldn't create trigger listener for {uid}: {e}")

        self._listener_refs = []

    def initialize(self, actions: dict[str, LLMActionData] = []):
        self.actions = actions
        self.llm = LLMAgent(self.app_name, self.uid, self.toolset, actions)

    def add_listener(self, trigger_name: str, handler, config: Optional[dict] = None):
        if not self.listener:
            return

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
        asyncio.create_task(self._async_stop_listener())
        del self._listener_refs
        await self._stop_impl()

    async def _async_stop_listener(self):
        if not self.listener:
            return

        try:
            self.listener.stop()
        except Exception as e:
            self.logger.error(f"Error while stopping listener: {e}")

    @abstractmethod
    async def _stop_impl(self):
        pass
