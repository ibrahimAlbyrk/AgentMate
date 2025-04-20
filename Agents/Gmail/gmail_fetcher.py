from typing import Dict, Any, List, Optional

from Core.logger import LoggerCreator
from Agents.LLM.llm_agent import LLMAgent


class GmailFetcher:
    """
    This class encapsulates all the logic for retrieving emails from Gmail,
    including fetching email lists and individual emails.
    """

    def __init__(self, llm_agent: LLMAgent, include_labels: List[str] = None):
        self.llm = llm_agent
        self.include_labels = include_labels or ['INBOX']
        self.logger = LoggerCreator.create_advanced_console("GmailFetcher")

    async def get_emails(self, limit: int) -> Dict[str, Any]:
        try:
            output = await self.llm.run_action("get_emails", max_results=limit, label_ids=self.include_labels)
            return output['data']
        except Exception as e:
            self.logger.error(f"Error fetching emails: {str(e)}")
            return {'messages': []}

    async def get_emails_subjects(self, limit: int) -> Dict[str, Any]:
        try:
            output = await self.llm.run_action("get_emails_subjects", max_results=limit, label_ids=self.include_labels)
            return output['data']
        except Exception as e:
            self.logger.error(f"Error fetching email subjects: {str(e)}")
            return {'messages': []}

    async def get_email_by_message_id(self, message_id: str) -> Dict[str, Any]:
        try:
            output = await self.llm.run_action("get_email_by_message_id", message_id=message_id)
            return output['data']
        except Exception as e:
            self.logger.error(f"Error fetching email by message ID: {str(e)}")
            return {}