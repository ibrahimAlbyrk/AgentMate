import traceback
from typing import Any, Dict, List

from Core.logger import LoggerCreator
from Core.Models.domain import Event, EventType

from Connectors.omi_connector import MemoryData, ConversationData
from Engines.email_classifier_engine import EmailClassifierEngine
from Engines.email_memory_summarizer_engine import EmailMemorySummarizerEngine

from DB.database import AsyncSessionLocal
from DB.Services.user_settings_service import UserSettingsService
from DB.Services.processed_gmail_service import ProcessedGmailService

from Plugins.plugin_interface import IPlugin
from Plugins.subscriber_plugin import SubscriberPlugin

logger = LoggerCreator.create_advanced_console("GmailSubscriber")

summarizer = EmailMemorySummarizerEngine()
classifier = EmailClassifierEngine()


class GmailSubscriber(SubscriberPlugin):
    name = "gmail"
    priority = 90
    dependencies = ["omi", "event_bus", "task_runner"]
    enabled_by_default = True

    def __init__(self):
        self.omi = None
        self.event_bus = None
        self.task_runner = None

    @classmethod
    async def create(cls, **kwargs) -> IPlugin:
        instance = cls()

        instance.omi = kwargs["omi"]
        instance.event_bus = kwargs["event_bus"]
        instance.task_runner = kwargs["task_runner"]

        await instance.event_bus.subscribe(EventType.GMAIL_SUMMARY, instance._handle_summary)
        await instance.event_bus.subscribe(EventType.GMAIL_CLASSIFY, instance._handle_classification)

        return instance

    async def _handle_summary(self, event: Event):
        try:
            data = event.data
            uid: str = data["uid"]
            emails: list[dict] = data["emails"]

            summaries = await summarizer.summarize_batch(uid, emails)

            await self.event_bus.publish_event(Event(
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

                print(classifications)

                # Filtering if these are important emails
                filtered_pairs = [
                    (email, classification)
                    for email, classification in zip(unprocessed, classifications)
                    if classification.get("answer", False)
                ]

                tasks = [
                    self.omi.create_conversation(uid, self._build_conversation(email, classification))
                    for email, classification in filtered_pairs
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
            text_source_spec=f"email about {classification.get(important)}" if classification.get(
                important) else "email",
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
            f"{('(Reply Required)' if reply_required else '')} {('(Links)' if has_links else '')} {('(Attachments)' if has_attachments else '')}",
            "## Content",
            content
        ]

        return "\n\n".join(part for part in parts if part.strip() != "")
