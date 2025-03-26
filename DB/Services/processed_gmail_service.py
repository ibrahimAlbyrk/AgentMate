from sqlalchemy.ext.asyncio import AsyncSession
from DB.Schemas.processed_data import ProcessedDataCreate
from DB.Repositories.processed_data import ProcessedDataRepository


class ProcessedGmailService:
    SERVICE_NAME = "gmail"

    @staticmethod
    async def has(session: AsyncSession, uid: str, gmail_id: str) -> bool:
        record = await ProcessedDataRepository.get(session, uid, ProcessedGmailService.SERVICE_NAME, gmail_id)
        return record is not None

    @staticmethod
    async def add(session: AsyncSession, uid: str, gmail_id: str, content: str = ""):
        data = ProcessedDataCreate(
            uid=uid,
            service=ProcessedGmailService.SERVICE_NAME,
            data_type=gmail_id,
            content=content
        )
        await ProcessedDataRepository.create_or_update(session, data)