from typing import Optional, List

from sqlalchemy import update
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from DB.Models.user_settings import UserSettings
from DB.Schemas.user_settings import UserSettingsCreate, UserSettingsUpdate


class UserSettingsRepository:

    @staticmethod
    async def get_all_users(session: AsyncSession) -> Optional[List[UserSettings]]:
        result = await session.execute(select(UserSettings))
        return result.scalars().all()

    @staticmethod
    async def get_user(uid: str, session: AsyncSession) -> Optional[List[UserSettings]]:
        result = await session.execute(
            select(UserSettings).where(UserSettings.uid == uid)
        )

        return result.scalars().all()

    @staticmethod
    async def get_by_service_id(session: AsyncSession, service_id: str) -> Optional[UserSettings]:
        result = await session.execute(
            select(UserSettings).where(UserSettings.service_id == service_id)
        )
        return result.scalars().first()

    @staticmethod
    async def get_by_uid_and_service(session: AsyncSession, uid: str, service_name: str) -> UserSettings | None:
        result = await session.execute(
            select(UserSettings).where(
                UserSettings.uid == uid,
                UserSettings.service_name == service_name
            )
        )
        return result.scalars().first()

    @staticmethod
    async def create_or_update(session: AsyncSession, data: UserSettingsCreate) -> UserSettings:
        existing = await UserSettingsRepository.get_by_uid_and_service(session, data.uid, data.service_name)

        if existing:
            stmt = (
                update(UserSettings)
                .where(UserSettings.uid == data.uid, UserSettings.service_name == data.service_name)
                .values(config=data.config)
                .execution_options(synchronize_session="fetch")
            )
            await session.execute(stmt)
        else:
            new_entry = UserSettings(**data.model_dump())
            session.add(new_entry)

        await session.commit()

        return await UserSettingsRepository.get_by_uid_and_service(session, data.uid, data.service_name)