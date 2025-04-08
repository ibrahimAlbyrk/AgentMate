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
    def __init__(self, app: App, uid: str, service_id: str, actions: [], processors: {}):
        self.uid = uid
        self.service_id = service_id

        self.tasks: dict[str, str] = {}

        self.processors = processors

        self.toolset = ComposioToolSet(api_key=settings.COMPOSIO_API_KEY)
        self.toolset.initiate_connection(app=app)
        try:
            self.tools = self.toolset.get_tools(actions=actions, processors=processors)
            print(f"Tools: {self.tools}")
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

                self.tools = self.toolset.get_tools(actions=actions, processors=processors)
                print(f"Tools: {self.tools}")

                composio_langchain.toolset.json_schema_to_model = original_json_schema_to_model
            else:
                logger.error(f"Failed to get tools: {e}")
                raise

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
        result = self.toolset.execute_action(Action.GMAIL_FETCH_EMAILS, {"max_results": 10, "page_token": "5"}, processors=self.processors)
        logger.debug(f"action result: {result}")
        return {}