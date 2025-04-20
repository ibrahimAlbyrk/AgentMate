import json
import asyncio
from typing import Dict, Any, Optional, Callable

from composio.client.collections import TriggerEventData

from Core.Utils.email_utils import EmailUtils
from Core.event_bus import EventBus
from Core.logger import LoggerCreator


class GmailEventHandler:
    def __init__(self, uid: str, event_bus: Optional[EventBus] = None):
        self.uid = uid
        self.event_bus = event_bus or EventBus()
        self.logger = LoggerCreator.create_advanced_console("GmailEventHandler")

    def handle_new_email_messages(self, event: TriggerEventData) -> None:
        try:
            raw_data = json.loads(event.model_dump_json())['payload']
            email = EmailUtils.decode_email(raw_data)

            data = {"uid": self.uid, "emails": [email]}
            asyncio.create_task(self._publish_event("gmail.inbox.classify", data))

            self.logger.debug(f"Processed new email: {email.get('subject', 'No subject')}")
        except Exception as e:
            self.logger.error(f"Error handling new email message: {str(e)}")

    async def _publish_event(self, channel: str, data: Dict[str, Any]) -> None:
        try:
            await self.event_bus.publish(channel, json.dumps(data))
        except Exception as e:
            self.logger.error(f"Error publishing event to {channel}: {str(e)}")

    def get_event_handlers(self) -> Dict[str, Callable[[TriggerEventData], None]]:
        return {
            "GMAIL_NEW_GMAIL_MESSAGE": self.handle_new_email_messages
        }