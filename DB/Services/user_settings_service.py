from typing import Optional
from sqlalchemy import select, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from DB.Schemas.gmail_config import GmailConfig
from DB.Models.user_settings import UserSettings
from DB.Schemas.user_settings import UserSettingsCreate
from DB.Repositories.user_settings import UserSettingsRepository


class UserSettingsService:
    @staticmethod
    async def get(session: AsyncSession, uid: str, service_name: str) -> Optional[UserSettings]:
        return await UserSettingsRepository.get_by_uid_and_service(session, uid, service_name)

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
    async def get_config(session: AsyncSession, uid: str, service_name: str) -> Optional[dict]:
        record = await UserSettingsService.get(session, uid, service_name)
        return record.config if record else None

    @staticmethod
    async def set_config(session: AsyncSession, uid: str, service_name: str, config: dict):
        data = UserSettingsCreate(uid=uid, service_name=service_name, config=config, is_logged_in=True, token_path="")
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
