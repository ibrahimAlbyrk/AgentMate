from typing import Dict, Any, List, Optional

from composio_openai import App, Action

from Core.EventBus import EventBus
from Core.logger import LoggerCreator

from Agents.LLM.llm_agent import LLMActionData
from Agents.Notion.notion_fetcher import NotionFetcher
from Agents.agent_interface import IAgent, AgentVersion
from Agents.Notion.notion_event_handler import NotionEventHandler

class NotionAgent(IAgent):
    def __init__(self, uid: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(uid, config)

        # Set up app name
        self.app_name = App.NOTION

        # Initialize components
        self.event_bus = EventBus()

        # Define LLM actions
        self.actions = {}

    async def _initialize_impl(self) -> bool:
        """
        Initialize the agent implementation.

        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            # Set up LLM actions
            self.actions = {"get_pages": LLMActionData(
                Action.NOTION_SEARCH_NOTION_PAGE,
                processors={}
            )}

            self.initialize_llm(self.actions)

            # Initialize components
            self.fetcher = NotionFetcher(self.llm)
            self.event_handler = NotionEventHandler(self.uid, self.event_bus)

            return True
        except Exception as e:
            self.logger.error(f"Error initializing Notion agent: {str(e)}")
            return False

    async def _run_impl(self) -> bool:
        try:
            events = await self.event_handler.get_events()
            for trigger_name, data in events.items():
                handler = data["handler"]
                config = data.get("config", {})
                self.add_listener(trigger_name, handler, config)

            return True
        except Exception as e:
            self.logger.error(f"Error running Notion agent: {str(e)}")
            return False

    async def _stop_impl(self) -> bool:
        try:
            self.logger.info(f"Notion agent stopped for user {self.uid}")
            return True
        except Exception as e:
            self.logger.error(f"Error stopping Notion agent: {str(e)}")
            return False

    async def get_pages(self) -> Dict[str, Any]:
        return await self.fetcher.get_pages()
