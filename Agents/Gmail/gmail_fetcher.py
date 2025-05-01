from typing import Dict, Any, List, Optional

from Core.logger import LoggerCreator

from Agents.LLM.llm_agent import LLMAgent
from Agents.agent_fetcher import AgentFetcher


class GmailFetcher(AgentFetcher):
    """
    This class encapsulates all the logic for retrieving emails from Gmail,
    including fetching email lists and individual emails.
    """

    def __init__(self, llm_agent: LLMAgent, include_labels: List[str] = None):
        super().__init__(llm_agent)
        self.include_labels = include_labels or ['INBOX']

    async def get_emails(self, limit: int) -> Dict[str, Any]:
        messages = await self.fetch("get_emails", limit=limit)

        if messages:
            return messages
        else:
            return {'messages': []}

    async def get_emails_subjects(self, limit: int) -> Dict[str, Any]:
        messages = await self.fetch("get_emails_subjects", max_results=limit, label_ids=self.include_labels)

        if messages:
            return messages
        else:
            return {'messages': []}

    async def get_email_by_message_id(self, message_id: str) -> Dict[str, Any]:
        messages = await self.fetch("get_email_by_message_id", message_id=message_id)

        if messages:
            return messages
        else:
            return {}