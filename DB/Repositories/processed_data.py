from sqlalchemy import update
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from DB.Models.processed_data import ProcessedData
from DB.Schemas.processed_data import ProcessedDataCreate


class ProcessedDataRepository:

    @staticmethod
    async def get(session: AsyncSession, uid: str, service: str, data_type: str) -> ProcessedData | None:
        result = await session.execute(
            select(ProcessedData).where(
                ProcessedData.uid == uid,
                ProcessedData.service == service,
                ProcessedData.data_type == data_type
            )
        )
        return result.scalars().first()

    @staticmethod
    async def create_or_update(session: AsyncSession, data: ProcessedDataCreate) -> ProcessedData:
        existing = await ProcessedDataRepository.get(session, data.uid, data.service, data.data_type)

        if existing:
            stmt = (
                update(ProcessedData)
                .where(
                    ProcessedData.uid == data.uid,
                    ProcessedData.service == data.service,
                    ProcessedData.data_type == data.data_type
                )
                .values(content=data.content)
                .execution_options(synchronize_session="fetch")
            )
            await session.execute(stmt)
        else:
            new_entry = ProcessedData(**data.model_dump())
            session.add(new_entry)

        await session.commit()
        return await ProcessedDataRepository.get(session, data.uid, data.service, data.data_type)