import json
import asyncio
from typing import Dict, Any, Optional, Callable

from sqlalchemy.ext.asyncio import AsyncSession

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


    async def get_events(self) -> Dict[str, Dict[str, Any]]:
        page_ids = self._get_page_ids(data=None)

        events = {}
        for page_id in page_ids:
            event = self._get_event_for_page(page_id)
            events.update(event)

        return events

    def _get_event_for_page(self, page_id) -> Dict[str, Any]:
        return {
            "NOTION_PAGE_ADDED_TRIGGER": {
                "handler": self.handle_new_page_added,
                "config": {"parent_page_id": page_id}
            },
            "NOTION_PAGE_UPDATED_TRIGGER": {
                "handler": self.handle_page_updated,
                "config": {"parent_page_id": page_id}
            },
            "NOTION_PAGE_ADDED_TO_DATABASE": {
                "handler": self.handle_page_added_to_database,
                "config": {"parent_page_id": page_id}
            }
        }

    def _get_page_ids(self, data: Dict[str, Any]) -> List[str]:
        page_ids = [
            page["id"]
            for page in data["response_data"]["results"]
            if page["object"] == "page"
        ]

        return page_ids
