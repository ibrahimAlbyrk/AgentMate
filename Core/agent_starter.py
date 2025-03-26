from sqlalchemy.future import select
from Core.logger import LoggerCreator
from Core.agent_manager import AgentManager
from sqlalchemy.ext.asyncio import AsyncSession
from DB.Models.user_settings import UserSettings

logger = LoggerCreator.create_advanced_console("AgentStarter")

agent_manager = AgentManager()

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
        await agent_manager.start_all_for_user(uid, services)
    except Exception as e:
        logger.error(f"start_user_agents error: {str(e)}")
