from Agents.Gmail.gmail_agent import GmailAgent
from Agents.Notion.notion_agent import NotionAgent
# from Agents.Calendar.calendar_agent import CalenderAgent
# from Agents.Slack.slack_agent import SlackAgent

from Agents.agent_interface import IAgent

class AgentFactory:
    registry: dict[str, type[IAgent]] = {
        "gmail": GmailAgent,
        "notion": NotionAgent
        # "calendar": CalendarAgent,
        # "slack": SlackAgent,
    }

    @classmethod
    def create(cls, uid: str, service_name: str) -> IAgent | None:
        agent_class = cls.registry.get(service_name)
        return agent_class(uid) if agent_class else None

    @classmethod
    def create_all(cls, uid: str, services: list[str]) -> list[IAgent]:
        return [cls.create(uid, service) for service in services if cls.create(uid, service) is not None]