from typing import Dict, Any

from Core.logger import LoggerCreator

from Agents.LLM.llm_agent import LLMAgent
from Agents.agent_fetcher import AgentFetcher


class OutlookFetcher(AgentFetcher):
    """Fetch emails and related data from Outlook."""

    def __init__(self, llm_agent: LLMAgent):
        super().__init__(llm_agent)

    async def get_emails(self, limit: int) -> Dict[str, Any]:
        messages = await self.fetch("get_emails", limit=limit)
        return messages if messages else {"messages": []}

    async def get_emails_subjects(self, limit: int) -> Dict[str, Any]:
        messages = await self.fetch("get_emails_subjects", limit=limit)
        return messages if messages else {"messages": []}

    async def get_email_by_message_id(self, message_id: str) -> Dict[str, Any]:
        messages = await self.fetch("get_email_by_message_id", message_id=message_id)
        return messages if messages else {}
