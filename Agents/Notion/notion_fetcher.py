from typing import Dict, Any, List, Optional

from Core.logger import LoggerCreator

from Agents.LLM.llm_agent import LLMAgent
from Agents.agent_fetcher import AgentFetcher

class NotionFetcher(AgentFetcher):
    def __init__(self, llm_agent: LLMAgent):
        super().__init__(llm_agent)

    async def get_pages(self) -> Dict[str, Any]:
        pages = await self.fetch("get_pages")
        return pages