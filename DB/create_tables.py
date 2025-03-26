import asyncio
from DB.database import engine
from DB.Models.base import BaseModel
from Core.logger import LoggerCreator
from Models import user_settings, processed_data

logger = LoggerCreator.create_advanced_console("TableCreator")

async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)
        logger.info("Tables are successfully created.")

if __name__ == "__main__":
    asyncio.run(init_models())