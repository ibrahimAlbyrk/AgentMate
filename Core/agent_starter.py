from sqlalchemy.future import select
from Core.logger import LoggerCreator
from sqlalchemy.ext.asyncio import AsyncSession
from DB.Models.user_settings import UserSettings

from Core.event_bus import EventBus

logger = LoggerCreator.create_advanced_console("AgentStarter")
event_bus = EventBus()

async def start_user_agents(uid: str, session: AsyncSession):
    try:
        result = await session.execute(
            select(UserSettings.service_name).where(UserSettings.uid == uid)
        )
        services = [row[0] for row in result.all()]

        if not services:
            logger.debug(f"No services registered for uid: {uid}")
            return

        logger.debug(f"Starting agents for {uid}: {services}")

        event_message = {"uid": uid, "services": services}
        await event_bus.publish("agent.start_all", event_message)

    except Exception as e:
        logger.error(f"start_user_agents error: {str(e)}")
