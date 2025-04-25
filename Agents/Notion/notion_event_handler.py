import json
import asyncio
from typing import Dict, Any, Optional, Callable

from DB.database import get_db

from Agents.agent_event_handler import AgentEventHandler

from Core.EventBus import EventBus
from Core.logger import LoggerCreator
from Core.Models import EventType, Event
from DB.Services.user_settings_service import UserSettingsService


class NotionEventHandler(AgentEventHandler):
    def __init__(self, uid: str, event_bus: Optional[EventBus] = None):
        super().__init__("Notion", uid, event_bus)

    def handle_new_page_added(self, raw_data: Dict[str, Any]) -> None:
        self.logger.debug("New page added")
        self.logger.debug(raw_data)
        pass

    def handle_page_updated(self, raw_data: Dict[str, Any]) -> None:
        self.logger.debug("page updated")
        self.logger.debug(raw_data)
        pass

    def handle_page_added_to_database(self, raw_data: Dict[str, Any]) -> None:
        self.logger.debug("page added to database")
        self.logger.debug(raw_data)
        pass


    def get_events(self) -> Dict[str, Dict[str, Any]]:

        user_config: Dict[str, Any] = UserSettingsService.get_config(get_db, self.uid, "notion")
        print(user_config)

        return {
            "NOTION_PAGE_ADDED_TRIGGER": {
                "handler": self.handle_new_page_added,
                "config": {}
            },
            "NOTION_PAGE_UPDATED_TRIGGER": {
                "handler": self.handle_page_updated,
                "config": {}
            },
            "NOTION_PAGE_ADDED_TO_DATABASE": {
                "handler": self.handle_page_added_to_database,
                "config": {}
            }
        }
