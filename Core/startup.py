from sqlalchemy.future import select
from Core.logger import LoggerCreator
from sqlalchemy.ext.asyncio import AsyncSession
from DB.Models.user_settings import UserSettings
from Core.agent_starter import start_user_agents, stop_user_agents

logger = LoggerCreator.create_advanced_console("StartupService")

async def start_all_user_agents(session: AsyncSession):
    try:
        result = await session.execute(
            select(UserSettings.uid)
            .where(UserSettings.is_logged_in == True)
            .distinct())
        uid_list = [row[0] for row in result.all()]

        # logger.debug(f"Starting agents for {len(uid_list)} registered user(s): {uid_list}")

        for uid in uid_list:
            await start_user_agents(uid, session)

    except Exception as e:
        logger.error(f"Error in startup agent runner: {str(e)}")


async def stop_all_user_agents(session: AsyncSession):
    try:
        result = await session.execute(
            select(UserSettings.uid)
            .where(UserSettings.is_logged_in == True)
            .distinct())
        uid_list = [row[0] for row in result.all()]

        # logger.debug(f"Stopping agents for {len(uid_list)} registered user(s): {uid_list}")

        for uid in uid_list:
            await stop_user_agents(uid, session)

    except Exception as e:
        logger.error(f"Error in startup agent runner: {str(e)}")
