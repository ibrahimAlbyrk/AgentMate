from Agents.gmail_agent import GmailAgent
# from Agents.notion_agent import NotionAgent
# from Agents.calendar_agent import CalenderAgent
# from Agents.slack_agent import SlackAgent

from Interfaces.agent_interface import IAgent

class AgentFactory:
    registry: dict[str, type[IAgent]] = {
        "gmail": GmailAgent,
        # "notion": NotionClient,
        # "calendar": CalendarAgent,
        # "slack": SlackAgent,
    }

    @classmethod
    def create(cls, service_name: str) -> IAgent | None:
        agent_class = cls.registry.get(service_name)
        return agent_class() if agent_class else None

    @classmethod
    def create_all(cls, service_names: list[str]) -> list[IAgent]:
        return [cls.create(name) for name in service_names if cls.create(name) is not None]