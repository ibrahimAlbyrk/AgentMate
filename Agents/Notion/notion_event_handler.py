import json
import asyncio
from typing import Dict, Any, Optional, Callable

from Agents.agent_event_handler import AgentEventHandler

from Core.EventBus import EventBus
from Core.logger import LoggerCreator
from Core.Models import EventType, Event

class NotionEventHandler(AgentEventHandler):
    def __init__(self, uid: str, event_bus: Optional[EventBus] = None):
        super().__init__("Notion", uid, event_bus)

    def handle_new_page_added(self, raw_data: Dict[str, Any]) -> None:
        pass

    def handle_page_updated(self, raw_data: Dict[str, Any]) -> None:
        pass

    def handle_page_added_to_database(self, raw_data: Dict[str, Any]) -> None:
        pass


    def get_event_handlers(self) -> Dict[str, Callable[[Dict[str, Any]], None]]:
        return {
            "NOTION_PAGE_ADDED_TRIGGER": self.handle_new_page_added,
            "NOTION_PAGE_UPDATED_TRIGGER": self.handle_page_updated,
            "NOTION_PAGE_ADDED_TO_DATABASE": self.handle_page_added_to_database
        }
