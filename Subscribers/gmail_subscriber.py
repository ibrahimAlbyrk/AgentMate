import json
import traceback

from Core.event_bus import EventBus
from Core.logger import LoggerCreator
from Core.task_runner import TaskRunner

from DB.database import AsyncSessionLocal

from Connectors.omi_connector import OmiConnector, MemoryData, ConversationData
from Engines.ai_engine import EmailMemorySummarizerEngine, EmailClassifierEngine

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
    async def register(self):
        self.event_bus.subscribe("gmail.inbox.summary", _handle_gmail_summary)
        self.event_bus.subscribe("gmail.inbox.classify", _handle_gmail_classification)


async def _handle_gmail_summary(raw_data: str):
    try:
        payload = json.loads(raw_data)
        uid: str = payload["uid"]
        emails: list[dict] = payload["emails"]

        summaries = await summarizer.summarize_batch(uid, emails)

        event_message = {"uid": uid, "memories": summaries}
        await event_bus.publish("websocket.gmail.memory",json.dumps(event_message))

        tasks = _build_memory_tasks(uid, summaries)

        await task_runner.run_async_tasks(tasks)

    except Exception as e:
        import traceback
        logger.error(f"Error handling gmail inbox: {str(e)}\n{traceback.format_exc()}")


def _build_memory_tasks(uid: str, summaries: list[str]):
    return [
        omi.create_memory(uid, MemoryData(
            text=summary,
            text_source="other",
            text_source_spec="learning from emails"
        )) for summary in summaries
    ]


async def _handle_gmail_classification(raw_data: str):
    try:
        payload = json.loads(raw_data)
        uid = payload["uid"]
        emails = payload["emails"]

        async with AsyncSessionLocal() as session:
            unprocessed_emails = []
            for email in emails:
                gmail_id = email.get("id")
                if not await ProcessedGmailService.has(session, uid, gmail_id):
                    unprocessed_emails.append(email)

            if not unprocessed_emails:
                logger.debug(f"No new emails to classify for {uid}")
                return

            gmail_config = await UserSettingsService.get_gmail_config(session, uid)
            important_categories = gmail_config.important_categories
            ignored_categories = gmail_config.ignored_categories

            classifications = await classifier.classify_batch(uid, unprocessed_emails, important_categories,
                                                              ignored_categories)

            if not classifications or len(classifications) != len(unprocessed_emails):
                logger.error(f"Classification result mismatch or failed for UID: {uid}")
                return

            conversation_tasks = [
                omi.create_conversation(uid, _build_conversation(email, classification))
                for email, classification in zip(unprocessed_emails, classifications)
            ]

            await task_runner.run_async_tasks(conversation_tasks)

            for email in unprocessed_emails:
                gmail_id = email.get("id")
                await ProcessedGmailService.add(session, uid, gmail_id)


    except Exception as e:
        logger.error(f"Error in handle_gmail_classification: {str(e)}\n{traceback.format_exc()}")


def _build_conversation(email, classification) -> ConversationData:
    date = email.get("date", None)
    language = classification.get("language", 'en')
    important = classification.get("important", None)

    text = _compose_email_text(email, classification)

    return ConversationData(
        started_at=date,
        text=text,
        text_source="other_text",
        text_source_spec=f"email about {classification.get(important)}" if classification.get(important) else "email",
        language=language
    )


def _compose_email_text(email: dict, classification: dict) -> str:
    subject = email.get('subject', '')
    sender = email.get('from', '')
    content = extract_plain_text_content(email.get("payload", {}))
    important = classification.get('important', None)
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


import base64
def extract_plain_text_content(payload):
    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/plain":
            encoded_data = part["body"].get("data", "")
            if encoded_data:
                decoded_bytes = base64.urlsafe_b64decode(encoded_data)
                return decoded_bytes.decode("utf-8")
    return ""