import asyncio
import json
from typing import Optional

from composio.client.collections import TriggerEventData

from Agents.LLM.llm_agent import LLMActionData
from Core.event_bus import EventBus
from Gmail.gmail_service import GmailService
from DB.database import AsyncSessionLocal
from Interfaces.agent_interface import IAgent
from DB.Services.user_settings_service import UserSettingsService
from Connectors.omi_connector import OmiConnector, ConversationData
from DB.Services.processed_gmail_service import ProcessedGmailService

from Core.event_bus import EventBus

from composio_openai import App, Action

from DB.Services.user_settings_service import UserSettingsService

event_bus = EventBus()


class GmailAgent(IAgent):
    def __init__(self, uid: str, service_id):
        super().__init__(uid, service_id)
        self.app_name = App.GMAIL

        actions = {
            "get_emails": LLMActionData(Action.GMAIL_FETCH_EMAILS,
                                        processors={"post": {Action.GMAIL_FETCH_EMAILS: self._gmails_postprocessor}}),
            "get_emails_subjects": LLMActionData(Action.GMAIL_FETCH_EMAILS,
                                                 processors={"post": {Action.GMAIL_FETCH_EMAILS: self._gmail_subjects_postprocessor}}),
            "get_email_by_message_id": LLMActionData(Action.GMAIL_FETCH_MESSAGE_BY_MESSAGE_ID,
                                                 processors={}),
        }

        self.initialize_llm(actions)

    async def _run_impl(self):
        # LISTENERS
        self.add_listener("GMAIL_NEW_GMAIL_MESSAGE", self._handle_new_email_messages)

    async def _stop_impl(self):
        pass

    async def get_emails(self,limit: int):
        return await self.llm.run_action("get_emails", max_results=limit)

    async def get_emails_subjects(self, offset: int, limit: int):
        return await self.llm.run_action("get_emails_subjects", page_token=str(offset), max_results=limit)

    async def get_email_by_message_id(self, message_id: str):
        return await self.llm.run_action("get_email_by_message_id", message_id=message_id)

    async def _handle_new_email_messages(self, event: TriggerEventData):
        try:
            raw_data = event.model_dump_json()
            data = json.loads(raw_data)
            payload = data["payload"]
            email = self.decode_email(payload)

            data = {"uid": self.uid, "emails": [email]}
            event_message = json.dumps(data)
            await event_bus.publish("gmail.inbox.classify", event_message)
        except Exception as e:
            self.logger.error(f"Error handling new email message: {str(e)}")

    @staticmethod
    def decode_email(payload: dict) -> dict:
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

    def _gmail_subjects_postprocessor(self, result: dict) -> dict:
        return self._filter_gmail_fields(result, fields=["subject", "messageId"])

    def _gmails_postprocessor(self, result: dict) -> dict:
        return self._filter_gmail_fields(result, fields=[
            "messageTimestamp", "messageId", "subject", "sender", "body"
        ])

    def _gmail_postprocessor(self, result: dict) -> dict:
        return self._filter_gmail_field(result, fields=[
            "messageTimestamp", "messageId", "subject", "sender", "body"
        ])

    @staticmethod
    def _filter_gmail_fields(result: dict, fields: list[str]) -> dict:
        processed_result = result.copy()
        processed_response = []

        for email in result["data"]["messages"]:
            filtered_email = {field: email[field] for field in fields if field in email}
            processed_response.append(filtered_email)

        processed_result["data"] = processed_response
        return processed_result

    @staticmethod
    def _filter_gmail_field(result: dict, fields: list[str]) -> dict:
        processed_result = result.copy()

        email = result["data"]
        processed_email = {field: email[field] for field in fields if field in email}

        processed_result["data"] = processed_email
        return processed_result
