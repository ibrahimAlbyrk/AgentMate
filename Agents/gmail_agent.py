import json
import base64
import asyncio

from bs4 import BeautifulSoup

from typing import Optional, Any

from composio.client.collections import TriggerEventData

from Agents.LLM.llm_agent import LLMActionData
from Core.event_bus import EventBus
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
        self.DEFAULT_EMAIL_FILTER = ["messageTimestamp", "messageId", "subject", "sender", "payload"]

        actions = {
            "get_emails": LLMActionData(Action.GMAIL_FETCH_EMAILS,
                                        processors={"post": {Action.GMAIL_FETCH_EMAILS: self._gmails_postprocessor}}),
            "get_emails_subjects": LLMActionData(Action.GMAIL_FETCH_EMAILS,
                                                 processors={"post": {Action.GMAIL_FETCH_EMAILS: self._gmail_subjects_postprocessor}}),
            "get_email_by_message_id": LLMActionData(Action.GMAIL_FETCH_MESSAGE_BY_MESSAGE_ID,
                                                 processors={"post": {Action.GMAIL_FETCH_MESSAGE_BY_MESSAGE_ID: self._gmail_postprocessor}}),
        }

        self.initialize_llm(actions)

    async def _run_impl(self):
        # LISTENERS
        self.add_listener("GMAIL_NEW_GMAIL_MESSAGE", self._handle_new_email_messages)

    async def _stop_impl(self):
        pass

    async def get_emails(self, limit: int) -> dict[str, Any]:
        output = await self.llm.run_action("get_emails", max_results=limit)
        emails = output['data']
        return emails

    async def get_emails_subjects(self, limit: int) -> dict[str, Any]:
        output = await self.llm.run_action("get_emails_subjects", max_results=limit)
        subjects = output['data']
        return subjects

    async def get_email_by_message_id(self, message_id: str) -> dict[str, Any]:
        output = await self.llm.run_action("get_email_by_message_id", message_id=message_id)
        email = output['data']
        return email

    def _handle_new_email_messages(self, event: TriggerEventData):
        try:
            raw_data = event.model_dump_json()
            data = json.loads(raw_data)
            payload = data["payload"]
            email = self.decode_email(payload)

            data = {"uid": self.uid, "emails": [email]}
            event_message = json.dumps(data)
            asyncio.run(event_bus.publish("gmail.inbox.classify", event_message))
        except Exception as e:
            self.logger.error(f"Error handling new email message: {str(e)}")

    def decode_email(self, payload: dict) -> dict:
        date = payload.get("messageTimestamp")
        msg_id = payload.get("messageId")
        subject = payload.get("subject")
        sender = payload.get("sender")
        payload = payload.get("payload")
        raw_body = self._extract_message_body(payload)
        body = self.strip_html_tags(raw_body)

        return {
            'id': msg_id,
            'date': date,
            'subject': subject,
            'sender': sender,
            'body': body
        }

    def _gmail_subjects_postprocessor(self, result: dict) -> dict:
        return self._filter_gmail_fields(result, fields=["subject", "messageId"])

    def _gmails_postprocessor(self, result: dict) -> dict:
        processed_result = result.copy()
        processed_response = []

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

    def _filter_and_process_email(self, email: dict, fields: list[str]) -> dict:
        filtered_email = {field: email[field] for field in fields if field in email}

        payload = filtered_email.get("payload")
        if payload:
            raw_body = self._extract_message_body(payload)
            body = self.strip_html_tags(raw_body or "")
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

    @staticmethod
    def _extract_message_body(payload, prefer_html=True):
        def decode(data):
            return base64.urlsafe_b64decode(data.encode("ASCII")).decode("utf-8")

        def get_part(parts):
            for part in parts:
                mime_type = part.get("mimeType", "")
                data = part.get("body", {}).get("data")

                if part.get("parts"):
                    result = get_part(part["parts"])
                    if result:
                        return result
                elif (prefer_html and mime_type == "text/html") or (not prefer_html and mime_type == "text/plain"):
                    if data:
                        return decode(data)
            return None

        if payload.get("body", {}).get("data"):
            return decode(payload["body"]["data"])

        if "parts" in payload:
            return get_part(payload["parts"])

        return None

    @staticmethod
    def strip_html_tags(html: str) -> str:
        return BeautifulSoup(html, "html.parser").get_text()