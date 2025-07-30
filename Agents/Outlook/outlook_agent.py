from typing import Dict, Any, Optional

from composio_openai import App, Action

from Core.EventBus import EventBus

from Agents.LLM.llm_agent import LLMActionData
from Agents.agent_interface import IAgent, AgentVersion
from Agents.Outlook.outlook_fetcher import OutlookFetcher
from Agents.Outlook.outlook_processor import OutlookProcessor
from Agents.Outlook.outlook_event_handler import OutlookEventHandler


class OutlookAgent(IAgent):
    """Agent for interacting with Microsoft Outlook."""

    VERSION = AgentVersion()
    DEPENDENCIES = []
    CONFIG_SCHEMA = {}

    def __init__(self, uid: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(uid, config)

        self.app_name = App.OUTLOOK

        self.event_bus = EventBus()
        self.actions = {}

    async def _initialize_impl(self) -> bool:
        try:
            self.actions = {
                "get_emails": LLMActionData(
                    Action.OUTLOOK_OUTLOOK_LIST_MESSAGES,
                    processors={"post": {Action.OUTLOOK_OUTLOOK_LIST_MESSAGES: self._process_emails}},
                ),
                "get_emails_subjects": LLMActionData(
                    Action.OUTLOOK_OUTLOOK_LIST_MESSAGES,
                    processors={"post": {Action.OUTLOOK_OUTLOOK_LIST_MESSAGES: self._process_email_subjects}},
                ),
                "get_email_by_message_id": LLMActionData(
                    Action.OUTLOOK_OUTLOOK_GET_MESSAGE,
                    processors={"post": {Action.OUTLOOK_OUTLOOK_GET_MESSAGE: self._process_email}},
                ),
            }

            self.initialize_llm(self.actions)

            self.processor = OutlookProcessor()
            self.fetcher = OutlookFetcher(self.llm)
            self.event_handler = OutlookEventHandler(self, self.uid, self.event_bus)

            return True
        except Exception as e:
            self.logger.error(f"Error initializing Outlook agent: {str(e)}")
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
            self.logger.error(f"Error running Outlook agent: {str(e)}")
            return False

    async def _stop_impl(self) -> bool:
        try:
            self.logger.info(f"Outlook agent stopped for user {self.uid}")
            return True
        except Exception as e:
            self.logger.error(f"Error stopping Outlook agent: {str(e)}")
            return False

    async def get_emails(self, limit: int) -> Dict[str, Any]:
        return await self.fetcher.get_emails(limit)

    async def get_emails_subjects(self, limit: int) -> Dict[str, Any]:
        return await self.fetcher.get_emails_subjects(limit)

    async def get_email_by_message_id(self, message_id: str) -> Dict[str, Any]:
        return await self.fetcher.get_email_by_message_id(message_id)

    def _process_emails(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return self.processor.process_emails(result)

    def _process_email(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return self.processor.process_email(result)

    def _process_email_subjects(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return self.processor.process_email_subjects(result)
