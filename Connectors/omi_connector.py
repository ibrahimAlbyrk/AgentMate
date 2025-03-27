import httpx
from typing import Optional
from Core.config import settings
from Core.logger import LoggerCreator
from datetime import datetime, timezone


class MemoryData:
    def __init__(self, text: str, text_source: str, text_source_spec: Optional[str] = ""):
        self.text = text
        self.text_source = text_source
        self.text_source_spec = text_source_spec


class ConversationData:
    def __init__(self,
                 text: str,
                 text_source: str,
                 text_source_spec: Optional[str] = "",
                 started_at: Optional[str] = None,
                 finished_at: Optional[str] = None,
                 language: Optional[str] = "en"):
        if started_at is None:
            started_at = datetime.now(timezone.utc).isoformat()

        if finished_at is None:
            finished_at = datetime.now(timezone.utc).isoformat()

        self.started_at = started_at
        self.finished_at = finished_at

        self.language = language

        self.text = text
        self.text_source = text_source
        self.text_source_spec = text_source_spec


class OmiConnector:
    def __init__(self):
        self.base_url = "https://api.omi.me"
        self.api_key = settings.OMI_API_KEY
        self.app_id = settings.OMI_APP_ID
        self.logger = LoggerCreator.create_advanced_console("OmiConnector")

    async def create_memory(self, uid: str, data: MemoryData):
        url = f"{self.base_url}/v2/integrations/{self.app_id}/user/memories?uid={uid}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "text": data.text,
            "text_source": data.text_source,
            "text_source_spec": data.text_source_spec
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            self.logger.debug(f"Memory creation response: {response.status_code} - {response.text}")
            return response

    async def create_conversation(self, uid: str, data: ConversationData):
        url = f"{self.base_url}/v2/integrations/{self.app_id}/user/conversations?uid={uid}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "started_at": data.started_at,
            "finished_at": data.finished_at,
            "language": data.language,
            "text": data.text,
            "text_source": data.text_source,
            "text_source_spec": data.text_source_spec
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            self.logger.debug(f"Conversation creation response: {response.status_code} - {response.text}")
            return response
