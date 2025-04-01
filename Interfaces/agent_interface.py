from typing import Optional
from Core.config import settings
from abc import ABC, abstractmethod
from composio_openai import ComposioToolSet, App, Action
from DB.Services.user_settings_service import UserSettingsService

toolset = ComposioToolSet(api_key=settings.COMPOSIO_API_KEY)

class IAgent(ABC):
    def __init__(self, uid: str, service_id):
        self.uid = uid
        self.service_id = service_id

        self.entity = toolset.get_entity(uid)
        self.app_name: App = None

    @abstractmethod
    async def run(self):
        pass

    @abstractmethod
    async def stop(self):
        pass