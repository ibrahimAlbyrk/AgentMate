import json

from Core.event_bus import EventBus
from Core.logger import LoggerCreator

from DB.database import AsyncSessionLocal

from Connectors.omi_connector import OmiConnector, MemoryData, ConversationData
from Engines.ai_engine import EmailMemorySummarizerEngine, EmailClassifierEngine

from DB.Services.user_settings_service import UserSettingsService
from DB.Services.processed_gmail_service import ProcessedGmailService

logger = LoggerCreator.create_advanced_console("GmailSubscriber")

event_bus = EventBus()

summarizer = EmailMemorySummarizerEngine()
classifier = EmailClassifierEngine()

omi = OmiConnector()


async def handle_gmail_summary(raw_data: str):
    try:
        payload = json.loads(raw_data)
        uid: str = payload["uid"]
        emails: list[dict] = payload["emails"]

        summaries = await summarizer.summarize_batch(emails)

        for summary in summaries:
            memory = MemoryData(
                text=summary,
                text_source="other",
                text_source_spec="learning from emails"
            )
            await omi.create_memory(uid, memory)

    except Exception as e:
        logger.error(f"Error handling gmail inbox: {str(e)}")


async def handle_gmail_classification(raw_data: str):
    try:
        payload = json.loads(raw_data)
        uid = payload["uid"]
        emails = payload["emails"]

        async with AsyncSessionLocal() as session:
            unprocessed_emails = []

            for index, email in enumerate(emails):
                gmail_id = email.get("id")
                if not await ProcessedGmailService.has(session, uid, gmail_id):
                    unprocessed_emails.append(email)

            if not unprocessed_emails:
                logger.debug(f"No new emails to classify for {uid}")
                return

            classifications = await classifier.classify_batch(unprocessed_emails)

            for i, email in enumerate(unprocessed_emails):
                classification = classifications[index]

                gmail_id = email.get("id")

                date = email.get("date", None)
                language = classification.get("language", None)
                important = classification.get('important', None)
                text = _compose_email_text(email, classification)

                conversation = ConversationData(
                    started_at=date,
                    text=text,
                    text_source="other_text",
                    text_source_spec=f"email about {important}" if important else "email",
                    language=language
                )

                await omi.create_conversation(uid, conversation)

                await ProcessedGmailService.add(
                    session=session,
                    uid=uid,
                    gmail_id=gmail_id,
                    # content=text[:200]
                )


    except Exception as e:
        logger.error(f"Error in handle_gmail_classification: {str(e)}")


async def register_subscribers():
    await event_bus.connect()
    event_bus.subscribe("gmail.inbox.summary", handle_gmail_summary)
    event_bus.subscribe("gmail.inbox.classify", handle_gmail_classification)
    await event_bus.listen()


def _compose_email_text(email: dict, classification: dict) -> str:
    subject = email.get('subject', '')
    sender = email.get('from', '')
    content = email.get('body', '')
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
