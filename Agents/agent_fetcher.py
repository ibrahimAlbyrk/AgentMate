from typing import Dict, Any, Optional

from Core.logger import LoggerCreator
from Agents.LLM.llm_agent import LLMAgent


class AgentFetcher:
    def __init__(self, llm_agent: LLMAgent):
        self.llm_agent = llm_agent
        self.logger = LoggerCreator.create_advanced_console(self.__class__.__name__)

    async def fetch(self, fetch_action: str, **params) -> Optional[Dict[str, Any]]:
        try:
            output = await self.llm_agent.run_action(fetch_action, **params)
            return output["data"]
        except Exception as e:
            self.logger.error(f"Failed to fetch {fetch_action}: {str(e)}")
            return {}
