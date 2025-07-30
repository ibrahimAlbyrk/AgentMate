import asyncio
from typing import Dict, Any, Optional

from Agents.agent_event_handler import AgentEventHandler
from Agents.agent_interface import IAgent

from Core.EventBus import EventBus
from Core.logger import LoggerCreator
from Core.Models import Event, EventType
from Core.Utils.email_utils import EmailUtils


class OutlookEventHandler(AgentEventHandler):
    """Event handler for Outlook events."""

    def __init__(self, agent: IAgent, uid: str, event_bus: Optional[EventBus] = None):
        super().__init__(agent, "Outlook", uid, event_bus)

    def handle_new_email_messages(self, raw_data: Dict[str, Any]) -> None:
        try:
            email = EmailUtils.decode_email(raw_data)
            asyncio.create_task(self.event_bus.publish_event(Event(
                type=EventType.MESSAGE_RECEIVED,
                data={"uid": self.uid, "emails": [email]},
            )))
            self.logger.debug(f"Processed new email: {email.get('subject', 'No subject')}")
        except Exception as e:
            self.logger.error(f"Error handling new email message: {str(e)}")

    async def get_events(self) -> Dict[str, Dict[str, Any]]:
        return {
            "OUTLOOK_OUTLOOK_MESSAGE_TRIGGER": {
                "handler": self.handle_new_email_messages,
                "config": {},
            }
        }
