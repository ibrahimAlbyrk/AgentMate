from typing import Optional
from Core.config import settings
from abc import ABC, abstractmethod
from composio_openai import ComposioToolSet, App, Action
from DB.Services.user_settings_service import UserSettingsService

toolset = ComposioToolSet(api_key=settings.COMPOSIO_API_KEY)

agent_listener = toolset.create_trigger_listener()

class IAgent(ABC):
    def __init__(self, uid: str, service_id):
        self.uid = uid
        self.service_id = service_id

        self.entity = toolset.get_entity(uid)
        entity.enable_trigger(
            app=app_name,
            trigger_name="GMAIL_NEW_GMAIL_MESSAGE",
            config={}
        )
        self.app_name: App = None

    async def run(self):
        await self._run_impl()
        agent_listener.wait_forever()
        print("listening...")

    @abstractmethod
    async def _run_impl(self):
       pass

    async def stop(self):
        agent_listener.stop()
        await self._stop_impl()

    @abstractmethod
    async def _stop_impl(self):
        pass
