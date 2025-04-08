import asyncio
import json
from typing import Optional

from composio.client.enums.action import Action
from composio.client.collections import TriggerEventData

from Core.event_bus import EventBus
from Core.logger import LoggerCreator
from Gmail.gmail_service import GmailService
from DB.database import AsyncSessionLocal
from Interfaces.agent_interface import IAgent
from DB.Services.user_settings_service import UserSettingsService
from Connectors.omi_connector import OmiConnector, ConversationData
from DB.Services.processed_gmail_service import ProcessedGmailService

from Core.event_bus import EventBus

from composio_openai import App

from DB.Services.user_settings_service import UserSettingsService

event_bus = EventBus()


class GmailAgent(IAgent):
    def __init__(self, uid: str, service_id):
        super().__init__(uid, service_id)
        self.app_name = App.GMAIL
        self.logger = LoggerCreator.create_standard("GmailAgent")

        actions = [
            'GMAIL_FETCH_EMAILS'
        ]

        self.initialize_llm(actions)

    async def _run_impl(self):
        # LISTENERS
        self.add_listener("GMAIL_NEW_GMAIL_MESSAGE", self._handle_new_email_messages)

        # TASKS
        self.llm.register_task("get_emails", "Skip the first {offset} emails and fetch the next {limit} emails from Gmail inbox")

    async def _stop_impl(self):
        pass

    async def get_emails(self, limit: int):
        return await self.llm.run_task("get_emails", offset=0, limit=limit)

    async def get_emails_with_offset(self, offset: int, limit: int):
        return await self.llm.run_task("get_emails", offset=offset, limit=limit)

    async def _handle_new_email_messages(self, event: TriggerEventData):
        try:
            raw_data = event.model_dump_json()
            data = json.loads(raw_data)
            payload = data["payload"]
            email = self._decode_email(payload)

            data = {"uid": self.uid, "emails": [email]}
            event_message = json.dumps(data)
            await event_bus.publish("gmail.inbox.classify", event_message)
        except Exception as e:
            self.logger.error(f"Error handling new email message: {str(e)}")

    @staticmethod
    def _decode_email(payload: dict) -> dict:
        date = payload.get("messageTimestamp")
        msg_id = payload.get("messageId")
        subject = payload.get("subject")
        sender = payload.get("sender")
        body = payload.get("messageText")

        return {
            'id': msg_id,
            'date': date,
            'subject': subject,
            'from': sender,
            'body': body
        }