import json

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from Core.logger import LoggerCreator
from Core.EventBus import EventBus
from Core.Models.domain import Event, EventType

from DB.Models.user_settings import UserSettings


logger = LoggerCreator.create_advanced_console("AgentStarter")
event_bus = EventBus()

async def start_user_agents(uid: str, session: AsyncSession):
    try:
        services = await _get_services(uid, session)

        logger.debug(f"Starting agents for {uid}: {services}")

        await event_bus.publish_event(Event(
            type=EventType.START_ALL_AGENT,
            data={"uid": uid, "services": services}
        ))

    except Exception as e:
        logger.error(f"start_user_agents error: {str(e)}")


async def stop_user_agents(uid: str, session: AsyncSession):
    try:
        services = await _get_services(uid, session)

        logger.debug(f"Stopping agents for {uid}: {services}")

        await event_bus.publish_event(Event(
            type=EventType.STOP_ALL_AGENT,
            data={"uid": uid, "services": services}
        ))

    except Exception as e:
        logger.error(f"start_user_agents error: {str(e)}")


async def _get_services(uid: str, session: AsyncSession) -> list:
    result = await session.execute(
        select(UserSettings.service_name)
        .where(UserSettings.uid == uid)
        .where(UserSettings.is_logged_in == True)
    )
    services = [row[0] for row in result.all()]

    if not services:
        logger.warning(f"No services registered for uid: {uid}")
        return []

    return services