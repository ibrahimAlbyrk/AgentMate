import json
import asyncio

from typing import Optional, Any

from composio.client.collections import TriggerEventData

from Agents.LLM.llm_agent import LLMActionData
from Core.EventBus import EventBus
from Core.Models.domain import Event, EventType
from DB.database import AsyncSessionLocal
from Interfaces.agent_interface import IAgent
from DB.Services.user_settings_service import UserSettingsService
from Connectors.omi_connector import OmiConnector, ConversationData
from DB.Services.processed_gmail_service import ProcessedGmailService

from Core.Utils.email_utils import EmailUtils

from composio_openai import App, Action

from DB.Services.user_settings_service import UserSettingsService

event_bus = EventBus()


class GmailAgent(IAgent):
    def __init__(self, uid: str):
        super().__init__(uid)

        self.app_name = App.GMAIL
        self.DEFAULT_EMAIL_FILTER = ["messageTimestamp", "messageId", "subject", "sender", "payload"]
        self.include_labels = ['INBOX']

        actions = {
            "get_emails": LLMActionData(Action.GMAIL_FETCH_EMAILS,
                                        processors={"post": {Action.GMAIL_FETCH_EMAILS: self._gmails_postprocessor}}),
            "get_emails_subjects": LLMActionData(Action.GMAIL_FETCH_EMAILS,
                                                 processors={"post": {Action.GMAIL_FETCH_EMAILS: self._gmail_subjects_postprocessor}}),
            "get_email_by_message_id": LLMActionData(Action.GMAIL_FETCH_MESSAGE_BY_MESSAGE_ID,
                                                 processors={"post": {Action.GMAIL_FETCH_MESSAGE_BY_MESSAGE_ID: self._gmail_postprocessor}}),
        }

        self.initialize(actions)

    async def _run_impl(self):
        # LISTENERS
        self.add_listener("GMAIL_NEW_GMAIL_MESSAGE", self._handle_new_email_messages)

    async def _stop_impl(self):
        pass

    async def get_emails(self, limit: int) -> dict[str, Any]:
        output = await self.llm.run_action("get_emails", max_results=limit, label_ids=self.include_labels)
        emails = output['data']
        return emails

    async def get_emails_subjects(self, limit: int) -> dict[str, Any]:
        output = await self.llm.run_action("get_emails_subjects", max_results=limit, label_ids=self.include_labels)
        subjects = output['data']
        return subjects

    async def get_email_by_message_id(self, message_id: str) -> dict[str, Any]:
        output = await self.llm.run_action("get_email_by_message_id", message_id=message_id)
        email = output['data']
        return email

    def _handle_new_email_messages(self, event: TriggerEventData):
        try:
            raw_data = json.loads(event.model_dump_json())['payload']
            email = EmailUtils.decode_email(raw_data)

            asyncio.run(event_bus.publish_event(Event(
                type=EventType.GMAIL_CLASSIFY,
                data={"uid": self.uid, "emails": [email]}
            )))
        except Exception as e:
            self.logger.error(f"Error handling new email message: {str(e)}")

    def _gmail_subjects_postprocessor(self, result: dict) -> dict:
        return self._filter_gmail_fields(result, fields=["subject", "messageId"])

    def _gmails_postprocessor(self, result: dict) -> dict:
        processed_result = result.copy()
        processed_response = []

        print(result["data"])

        for email in result["data"]["messages"]:
            processed_response.append(
                self._filter_and_process_email(email, fields=self.DEFAULT_EMAIL_FILTER)
            )

        processed_result["data"] = processed_response
        return processed_result

    def _gmail_postprocessor(self, result: dict) -> dict:
        processed_result = result.copy()

        email = result["data"]
        processed_result["data"] = self._filter_and_process_email(email, fields=self.DEFAULT_EMAIL_FILTER)

        return processed_result

    @staticmethod
    def _filter_and_process_email(email: dict, fields: list[str]) -> dict:
        filtered_email = {field: email[field] for field in fields if field in email}

        payload = filtered_email.get("payload")
        if payload:
            raw_body = EmailUtils.extract_message_body(payload)
            body = EmailUtils.strip_html_tags(raw_body or "")
            filtered_email["body"] = body
            del filtered_email["payload"]

        return filtered_email

    @staticmethod
    def _filter_gmail_fields(result: dict, fields: list[str]) -> dict:
        processed_result = result.copy()
        processed_response = []

        for email in result["data"]["messages"]:
            filtered_email = {field: email[field] for field in fields if field in email}
            processed_response.append(filtered_email)

        processed_result["data"] = processed_response
        return processed_result
