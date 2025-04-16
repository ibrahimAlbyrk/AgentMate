"""
Gmail Event Handler for AgentMate

This module provides functionality for handling Gmail events.
"""

import json
import asyncio
from typing import Dict, Any, Optional, Callable

from composio.client.collections import TriggerEventData

from Core.Utils.email_utils import EmailUtils
from Core.event_bus import EventBus
from Core.logger import LoggerCreator

class GmailEventHandler:
    """
    Responsible for handling Gmail events.
    
    This class encapsulates all the logic for handling events related to Gmail,
    such as new email notifications.
    """
    
    def __init__(self, uid: str, event_bus: Optional[EventBus] = None):
        """
        Initialize the Gmail event handler.
        
        Args:
            uid: The user ID
            event_bus: The event bus to use for publishing events
        """
        self.uid = uid
        self.event_bus = event_bus or EventBus()
        self.logger = LoggerCreator.create_advanced_console("GmailEventHandler")
    
    def handle_new_email_messages(self, event: TriggerEventData) -> None:
        """
        Handle new email message events.
        
        Args:
            event: The trigger event data
        """
        try:
            raw_data = json.loads(event.model_dump_json())['payload']
            email = EmailUtils.decode_email(raw_data)
            
            data = {"uid": self.uid, "emails": [email]}
            asyncio.create_task(self._publish_event("gmail.inbox.classify", data))
            
            self.logger.debug(f"Processed new email: {email.get('subject', 'No subject')}")
        except Exception as e:
            self.logger.error(f"Error handling new email message: {str(e)}")
    
    async def _publish_event(self, channel: str, data: Dict[str, Any]) -> None:
        """
        Publish an event to the event bus.
        
        Args:
            channel: The channel to publish to
            data: The data to publish
        """
        try:
            await self.event_bus.publish(channel, json.dumps(data))
        except Exception as e:
            self.logger.error(f"Error publishing event to {channel}: {str(e)}")
    
    def get_event_handlers(self) -> Dict[str, Callable[[TriggerEventData], None]]:
        """
        Get a dictionary of event handlers.
        
        Returns:
            A dictionary mapping event names to handler functions
        """
        return {
            "GMAIL_NEW_GMAIL_MESSAGE": self.handle_new_email_messages
        }