import json
import base64
import traceback

from Core.EventBus import EventBus
from Core.logger import LoggerCreator
from Core.task_runner import TaskRunner
from Core.Models.domain import Event, EventType


from Connectors.omi_connector import OmiConnector, MemoryData, ConversationData
from Engines.ai_engine import EmailMemorySummarizerEngine, EmailClassifierEngine

from DB.database import AsyncSessionLocal
from DB.Services.user_settings_service import UserSettingsService
from DB.Services.processed_gmail_service import ProcessedGmailService

from Subscribers.base_subscriber import BaseSubscriber

logger = LoggerCreator.create_advanced_console("GmailSubscriber")

event_bus = EventBus()

summarizer = EmailMemorySummarizerEngine()
classifier = EmailClassifierEngine()

omi = OmiConnector()
task_runner = TaskRunner()


class GmailSubscriber(BaseSubscriber):
    def __init__(self):
        self.omi = None
        self.event_bus = None
        self.task_runner = None

    async def setup(self, **services):
        self.omi = services["omi"]
        self.event_bus = services["event_bus"]
        self.task_runner = services["task_runner"]

        self.event_bus.subscribe(EventType.GMAIL_SUMMARY, self._handle_summary)
        self.event_bus.subscribe(EventType.GMAIL_CLASSIFY, self._handle_classification)


    async def _handle_summary(self, event: Event):
        try:
            data = event.data
            uid: str = data["uid"]
            emails: list[dict] = data["emails"]

            summaries = await summarizer.summarize_batch(uid, emails)

            await event_bus.publish_event(Event(
                type=EventType.WEBSOCKET_GMAIL_MEMORY,
                data={"uid": uid, "memories": summaries}
            ))

            tasks = [
                self.omi.create_memory(uid, MemoryData(
                    text=summary,
                    text_source="other",
                    text_source_spec="learning from emails"
                )) for summary in summaries
            ]

            await self.task_runner.run_async_tasks(tasks)

        except Exception as e:
            logger.error(f"Error in _handle_summary: {str(e)}\n{traceback.format_exc()}")


    async def _handle_classification(self, event: Event):
        try:
            data = event.data
            uid = data["uid"]
            emails = data["emails"]

            async with AsyncSessionLocal() as session:
                unprocessed = await self._filter_unprocessed_emails(session, uid, emails)
                if not unprocessed:
                    logger.debug(f"No new emails to classify for {uid}")
                    return

                config = await UserSettingsService.get_gmail_config(session, uid)

                classifications = await classifier.classify_batch(
                    uid, unprocessed,
                    config.important_categories,
                    config.ignored_categories
                )

                tasks = [
                    self.omi.create_conversation(uid, self._build_conversation(email, classification))
                    for email, classification in zip(unprocessed, classifications)
                ]

                await self.task_runner.run_async_tasks(tasks)

                for email in unprocessed:
                    await ProcessedGmailService.add(session, uid, email["id"])


        except Exception as e:
            logger.error(f"Error in handle_gmail_classification: {str(e)}\n{traceback.format_exc()}")

    @staticmethod
    async def _filter_unprocessed_emails(session, uid, emails):
        unprocessed = []
        for email in emails:
            if not await ProcessedGmailService.has(session, uid, email.get("id")):
                unprocessed.append(email)
        return unprocessed

    def _build_conversation(self, email, classification) -> ConversationData:
        date = email.get("date", None)
        language = classification.get("language", 'en')
        important = classification.get("important", None)

        text = self._compose_email_text(email, classification)

        return ConversationData(
            started_at=date,
            text=text,
            text_source="other_text",
            text_source_spec=f"email about {classification.get(important)}" if classification.get(important) else "email",
            language=language
        )

    @staticmethod
    def _compose_email_text(email: dict, classification: dict) -> str:
        subject = email.get('subject', '')
        sender = email.get('sender', '')
        content = email.get('body', '')
        important = classification.get('important', '')
        sender_importance = classification.get('sender_importance', '')
        priority = classification.get('priority', '')
        sentiment = classification.get('sentiment', '')
        tags = classification.get('tags', [])
        summary = classification.get('summary', '')
        has_attachments = classification.get('has_attachment', False)
        has_links = classification.get('has_links', False)
        suggested_actions = classification.get('suggested_actions', [])
        reply_required = classification.get('reply_required', False)

        suggested_actions_text = f"**Suggested Actions**: {', '.join(suggested_actions)}" if suggested_actions else ""

        parts = [
            f"# {subject}",
            f"**From**: {sender}",
            f"**Priority**: {priority}",
            f"**Tags**: {', '.join(tags) if tags else ''}",
            f"**Sentiment**: {sentiment}",
            f"**Sender Importance**: {sender_importance}",
            suggested_actions_text,
            "---",
            "## Summary",
            summary,
            "---",
            f"{'(Reply Required)' if reply_required else ''} {('(Links)' if has_links else '')} {('(Attachments)' if has_attachments else '')}",
            "## Content",
            content
        ]

        return "\n\n".join(part for part in parts if part.strip() != "")

    @staticmethod
    def extract_plain_text_content(payload):
        for part in payload.get("parts", []):
            if part.get("mimeType") == "text/plain":
                encoded_data = part["body"].get("data", "")
                if encoded_data:
                    decoded_bytes = base64.urlsafe_b64decode(encoded_data)
                    return decoded_bytes.decode("utf-8")
        return ""