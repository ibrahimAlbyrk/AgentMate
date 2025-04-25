from typing import Optional, List
from sqlalchemy import select, distinct, update
from sqlalchemy.ext.asyncio import AsyncSession
from Core.config import GmailConfig
from DB.Models.user_settings import UserSettings
from DB.Schemas.user_settings import UserSettingsCreate
from DB.Repositories.user_settings import UserSettingsRepository


class UserSettingsService:

    @staticmethod
    async def get_all_users(session: AsyncSession) -> Optional[List[UserSettings]]:
        return await UserSettingsRepository.get_all_users(session)

    @staticmethod
    async def get_user_by_uid(uid: str, session: AsyncSession) -> Optional[List[UserSettings]]:
        return await UserSettingsRepository.get_user(uid, session)

    @staticmethod
    async def get(session: AsyncSession, uid: str, service_name: str) -> Optional[UserSettings]:
        return await UserSettingsRepository.get_by_uid_and_service(session, uid, service_name)

    @staticmethod
    async def get_by_service_id(session: AsyncSession, service_id: str) -> Optional[UserSettings]:
        return await UserSettingsRepository.get_by_service_id(session, service_id)

    @staticmethod
    async def get_user_uids(session: AsyncSession) -> list[str]:
        result = await session.execute(
            select(distinct(UserSettings.uid))
        )
        return [row[0] for row in result.all()]

    @staticmethod
    async def has_any(session: AsyncSession, uid: str):
        result = await session.execute(
            select(UserSettings.uid).where(UserSettings.uid == uid)
        )
        return result.first() is not None

    @staticmethod
    async def has_service(session: AsyncSession, uid: str, service_name: str):
        result = await session.execute(
            select(UserSettings.uid)
            .where(
                UserSettings.uid == uid,
                UserSettings.service_name == service_name
            )
        )
        return result.first() is not None

    @staticmethod
    async def change_service_id(session: AsyncSession, uid: str, service_name: str, new_service_id: str) -> bool:
        try:
            stmt = (
                update(UserSettings)
                .where(UserSettings.uid == uid, UserSettings.service_name == service_name)
                .values(service_id=new_service_id)
            )
            await session.execute(stmt)
            await session.commit()
            return True
        except Exception:
            return False

    @staticmethod
    async def get_config(session: AsyncSession, uid: str, service_name: str) -> Optional[dict]:
        record = await UserSettingsService.get(session, uid, service_name)
        return record.config if record else None

    @staticmethod
    async def set_config(session: AsyncSession, uid: str, service_id: str, service_name: str, config: dict):
        data = UserSettingsCreate(uid=uid, service_id=service_id, service_name=service_name, config=config, is_logged_in=True, token_path="")
        await UserSettingsRepository.create_or_update(session, data)

    @staticmethod
    async def get_token_path(session: AsyncSession, uid: str, service_name: str) -> Optional[str]:
        record = await UserSettingsService.get(session, uid, service_name)
        return record.token_path if record else None

    @staticmethod
    async def set_token_path(session: AsyncSession, uid: str, service_name: str, token_path: str):
        record = await UserSettingsService.get(session, uid, service_name)
        if record:
            record.token_path = token_path
            await session.commit()

    @staticmethod
    async def is_logged_in(session: AsyncSession, uid: str, service_name: str) -> bool:
        record = await UserSettingsService.get(session, uid, service_name)
        return record.is_logged_in if record else False

    @staticmethod
    async def set_logged_in(session: AsyncSession, uid: str, service_name: str, status: bool):
        record = await UserSettingsService.get(session, uid, service_name)
        if record:
            record.is_logged_in = status
            await session.commit()

    # SERVICE CONFIGS
    @staticmethod
    async def get_gmail_config(session: AsyncSession, uid: str) -> GmailConfig:
        raw = await UserSettingsService.get_config(session, uid, "gmail")
        return GmailConfig(**(raw or {}))
