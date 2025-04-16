"""
Gmail Agent for AgentMate

This module provides the main Gmail agent implementation.
"""

from typing import Dict, Any, List, Optional

from composio_openai import App, Action

from Interfaces.agent_interface import IAgent, AgentVersion
from Agents.LLM.llm_agent import LLMActionData
from Core.event_bus import EventBus
from Core.logger import LoggerCreator

from Agents.Gmail.gmail_fetcher import GmailFetcher
from Agents.Gmail.gmail_processor import GmailProcessor
from Agents.Gmail.gmail_event_handler import GmailEventHandler

class GmailAgent(IAgent):
    """
    Gmail Agent for AgentMate.

    This agent is responsible for interacting with Gmail, including
    fetching emails, processing email data, and handling Gmail events.
    """

    # Class-level attributes for agent versioning and dependencies
    VERSION = AgentVersion()
    DEPENDENCIES = []
    CONFIG_SCHEMA = {
        "include_labels": {"type": "list", "default": ["INBOX"]},
        "max_emails": {"type": "integer", "default": 10}
    }

    def __init__(self, uid: str, service_id: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Gmail agent.

        Args:
            uid: The user ID
            service_id: The service ID
            config: Configuration for the agent
        """
        super().__init__(uid, service_id, config)

        # Set up app name
        self.app_name = App.GMAIL

        # Initialize components
        self.event_bus = EventBus()
        self.include_labels = self.config.get("include_labels", ["INBOX"])

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
            self.actions = {
                "get_emails": LLMActionData(
                    Action.GMAIL_FETCH_EMAILS,
                    processors={"post": {Action.GMAIL_FETCH_EMAILS: self._process_emails}}
                ),
                "get_emails_subjects": LLMActionData(
                    Action.GMAIL_FETCH_EMAILS,
                    processors={"post": {Action.GMAIL_FETCH_EMAILS: self._process_email_subjects}}
                ),
                "get_email_by_message_id": LLMActionData(
                    Action.GMAIL_FETCH_MESSAGE_BY_MESSAGE_ID,
                    processors={"post": {Action.GMAIL_FETCH_MESSAGE_BY_MESSAGE_ID: self._process_email}}
                ),
            }

            self.initialize_llm(self.actions)

            # Initialize components
            self.processor = GmailProcessor()
            self.fetcher = GmailFetcher(self.llm, self.include_labels)
            self.event_handler = GmailEventHandler(self.uid, self.event_bus)

            return True
        except Exception as e:
            self.logger.error(f"Error initializing Gmail agent: {str(e)}")
            return False

    async def _run_impl(self) -> bool:
        try:
            # Set up event listeners
            handlers = self.event_handler.get_event_handlers()
            for trigger_name, handler in handlers.items():
                self.add_listener(trigger_name, handler)

            self.logger.info(f"Gmail agent started for user {self.uid}")
            return True
        except Exception as e:
            self.logger.error(f"Error running Gmail agent: {str(e)}")
            return False

    async def _stop_impl(self) -> bool:
        try:
            self.logger.info(f"Gmail agent stopped for user {self.uid}")
            return True
        except Exception as e:
            self.logger.error(f"Error stopping Gmail agent: {str(e)}")
            return False

    # Email fetching methods

    async def get_emails(self, limit: int) -> Dict[str, Any]:
        return await self.fetcher.get_emails(limit)

    async def get_emails_subjects(self, limit: int) -> Dict[str, Any]:
        return await self.fetcher.get_emails_subjects(limit)

    async def get_email_by_message_id(self, message_id: str) -> Dict[str, Any]:
        return await self.fetcher.get_email_by_message_id(message_id)

    # Email processing methods (for LLM action post-processing)

    def _process_emails(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return self.processor.process_emails(result)

    def _process_email(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return self.processor.process_email(result)

    def _process_email_subjects(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return self.processor.process_email_subjects(result)
