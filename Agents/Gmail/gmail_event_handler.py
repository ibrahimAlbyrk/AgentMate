import json
import asyncio
from typing import Dict, Any, Optional, Callable

from Agents.agent_interface import IAgent
from Agents.agent_event_handler import AgentEventHandler

from Core.EventBus import EventBus
from Core.logger import LoggerCreator
from Core.Models import Event, EventType
from Core.Utils.email_utils import EmailUtils


class GmailEventHandler(AgentEventHandler):
    def __init__(self, agent: IAgent, uid: str, event_bus: Optional[EventBus] = None):
        super().__init__(agent, "Gmail", uid, event_bus)

    def handle_new_email_messages(self, raw_data: Dict[str, Any]) -> None:
        try:
            email = EmailUtils.decode_email(raw_data)

            asyncio.create_task(self.event_bus.publish_event(Event(
                type=EventType.GMAIL_CLASSIFY,
                data={"uid": self.uid, "emails": [email]},
            )))

            self.logger.debug(f"Processed new email: {email.get('subject', 'No subject')}")
        except Exception as e:
            self.logger.error(f"Error handling new email message: {str(e)}")

    async def get_events(self) -> Dict[str, Dict[str, Any]]:
        return {
            "GMAIL_NEW_GMAIL_MESSAGE": {
                "handler": self.handle_new_email_messages,
                "config": {}
            }
        }