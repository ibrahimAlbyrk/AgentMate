import asyncio
from DB.database import engine
from DB.Models.base import BaseModel
from Core.logger import LoggerCreator
from DB.Models import user_settings, processed_data

logger = LoggerCreator.create_advanced_console("TableCreator")

async def init_models():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(BaseModel.metadata.drop_all)
            await conn.run_sync(BaseModel.metadata.create_all)
            logger.info("Tables are successfully created.")
    except Exception as e:
        logger.error(f"Failed to create tables: {str(e)}")

if __name__ == "__main__":
    asyncio.run(init_models())