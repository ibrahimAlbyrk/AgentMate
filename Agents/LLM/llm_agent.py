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

class LLMAgent:
    def __init__(self, app:App, uid: str, service_id: str, actions: [], processors: {}):
        self.uid = uid
        self.service_id = service_id

        self.tasks: dict[str, str] = {}

        self.toolset = ComposioToolSet(api_key=settings.COMPOSIO_API_KEY)
        self.toolset.initiate_connection(app=app)
        self.tools = self.toolset.get_tools(actions=actions, processors=processors)

        agent = create_openai_functions_agent(llm, self.tools, prompt)
        self.executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True
        )

    def register_task(self, name: str, prompt: str):
        self.tasks[name] = prompt

    async def run_task(self, name: str, **kwargs) -> dict[str, Any]:
        if name not in self.tasks:
            raise ValueError(f"Task {name} not found")
        input_prompt = self.tasks[name].format(**kwargs)
        return await self.executor.ainvoke({"input": input_prompt})