import json
import asyncio
from typing import Dict, Any, Optional, Callable, List

from sqlalchemy.ext.asyncio import AsyncSession

from DB.database import get_db

from Agents.agent_event_handler import AgentEventHandler

from Agents.agent_interface import IAgent

from Core.EventBus import EventBus
from Core.logger import LoggerCreator
from Core.Models import EventType, Event
from DB.Services.user_settings_service import UserSettingsService


class NotionEventHandler(AgentEventHandler):
    def __init__(self, agent: IAgent, uid: str, event_bus: Optional[EventBus] = None):
        super().__init__(agent, "Notion", uid, event_bus)

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
        from Agents.Notion.notion_agent import NotionAgent
        if not isinstance(self.agent, NotionAgent):
            return {}

        pages = await self.agent.get_pages()

        ids = self._get_page_ids(data=pages)

        return self._get_events_for_pages(ids)

    def _get_events_for_pages(self, ids: Dict[str, list]) -> Dict[str, Any]:
        page_ids = ids.get("page_ids", [])
        database_ids = ids.get("database_ids", [])
        parent_page_ids = ids.get("parent_page_ids", [])

        events: Dict[str, Any] = {}

        for page_id in page_ids:
            event = {
                "NOTION_PAGE_UPDATED_TRIGGER": {
                "handler": self.handle_page_updated,
                "config": {"page_id": page_id}
                }
            }
            events.update(event)

        for database_id in database_ids:
            event = {
                "NOTION_PAGE_ADDED_TO_DATABASE": {
                    "handler": self.handle_new_page_added,
                    "config": {"database_id": database_id}
                }
            }
            events.update(event)

        for parent_page_id in parent_page_ids:
            event = {
                "NOTION_PAGE_ADDED_TRIGGER": {
                    "handler": self.handle_new_page_added,
                    "config": {"parent_page_id": parent_page_id}
                }
            }
            events.update(event)

        return events

    def _get_page_ids(self, data: Dict[str, Any]):
        page_ids = []
        database_ids = set()
        parent_page_ids = set()

        for page in data["data"]["response_data"]["results"]:
            page_ids.append(page["id"])
            parent = page.get("parent", {})

            if parent.get("type") == "database_id":
                database_ids.add(parent["database_id"])
            elif parent.get("type") == "page_id":
                parent_page_ids.add(parent["page_id"])

        return {
            "page_ids": page_ids,
            "database_ids": list(database_ids),
            "parent_page_ids": list(parent_page_ids)
        }
