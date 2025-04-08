from typing import Any

from langchain import hub
from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_functions_agent, AgentExecutor

from composio_langchain import ComposioToolSet, Action, App


from Core.config import settings
from Core.logger import LoggerCreator

llm = ChatOpenAI()
prompt = hub.pull("hwchase17/openai-functions-agent")
logger = LoggerCreator.create_advanced_console("LLMAgent")

class LLMAgent:
    def __init__(self, uid: str, service_id: str, actions: []):
        self.uid = uid
        self.service_id = service_id

        self.tasks: dict[str, str] = {}

        self.toolset = ComposioToolSet(api_key=settings.COMPOSIO_API_KEY)
        try:
            self.tools = self.toolset.get_tools(actions=actions)
        except TypeError as e:
            if "skip_default" in str(e):
                # logger.warning("Detected 'skip_default' parameter issue, trying workaround...")
                import inspect
                from functools import wraps
                import composio_langchain.toolset
                
                original_json_schema_to_model = composio_langchain.toolset.json_schema_to_model
                
                @wraps(original_json_schema_to_model)
                def wrapper(*args, **kwargs):
                    if "skip_default" in kwargs:
                        del kwargs["skip_default"]
                    return original_json_schema_to_model(*args, **kwargs)
                
                composio_langchain.toolset.json_schema_to_model = wrapper
                
                self.tools = self.toolset.get_tools(actions=actions)
                
                composio_langchain.toolset.json_schema_to_model = original_json_schema_to_model
            else:
                logger.error(f"Failed to get tools: {e}")
                raise

        agent = create_openai_functions_agent(llm, self.tools, prompt)
        self.executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=False
        )

    def register_task(self, name: str, prompt: str):
        self.tasks[name] = prompt

    async def run_task(self, name: str, **kwargs) -> dict[str, Any]:
        if name not in self.tasks:
            raise ValueError(f"Task {name} not found")
        input_prompt = self.tasks[name].format(**kwargs)
        return await self.executor.invoke({"input": input_prompt})