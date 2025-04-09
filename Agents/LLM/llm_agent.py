from typing import Any

from langchain import hub
from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_functions_agent, AgentExecutor

from composio_langchain import ComposioToolSet, Action, App

from Core.config import settings
from Core.logger import LoggerCreator

llm = ChatOpenAI(model="gpt-4o-mini")
prompt = hub.pull("hwchase17/openai-functions-agent")
logger = LoggerCreator.create_advanced_console("LLMAgent")

VERBOSE_DEBUG = True


class LLMActionData:
    def __init__(self, action: Action, processors: dict[str, Any]):
        self.action = action
        self.processors = processors


class LLMAgent:
    def __init__(self,
                 app: App,
                 uid: str,
                 service_id: str,
                 actions: dict[str, LLMActionData]):
        """
        - Actions: { Action Name: action data }
        - Processors: { Processor Name: {param name: param value} }
        """
        self.uid = uid
        self.service_id = service_id

        self.actions = actions
        self.action_names = [action_data.action for action_data in self.actions.values()]

        self.tasks: dict[str, str] = {}

        self.toolset = ComposioToolSet(api_key=settings.COMPOSIO_API_KEY)
        self.toolset.initiate_connection(app=app)

    async def run_action(self, action_name: str, **params) -> dict[str, LLMActionData]:
        llm_action_data: LLMActionData = None
        for name, action_data in self.actions.items():
            if name == action_name:
                llm_action_data = action_data
                break

        if llm_action_data is None:
            raise ValueError(f"Action {action_name} not found")

        action = llm_action_data.action
        processors = llm_action_data.processors

        result = self.toolset.execute_action(action, params, processors=processors)
        return result
